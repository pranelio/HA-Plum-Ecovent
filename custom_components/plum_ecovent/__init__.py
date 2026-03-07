"""Plum Ecovent integration entry point.

Minimal async setup and setup_entry placeholders.
"""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_AVAILABLE_REGISTERS,
    CONF_NON_RESPONDING_REGISTERS,
    CONF_UNSUPPORTED_REGISTERS,
    DOMAIN,
    CONF_UPDATE_RATE,
    DEFAULT_UPDATE_RATE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_OPTIONAL_DISABLE,
    CONF_RESPONDING_REGISTERS,
    CONF_DEVICE_SETTINGS_VALUES,
    CONF_DEVICE_SERIAL,
    CONF_DEVICE_NAME,
    CONF_FIRMWARE_VERSION,
    CONF_DEVICE_INFO_PENDING_FETCH,
    CONF_DEVICE_INFO_FETCH_ATTEMPTED,
)
from .device_info import decode_utf8_registers, format_firmware
from .modbus_client import ModbusClientManager
from .coordinator import PlumEcoventCoordinator
from .registers_loader import async_get_registers_module

# Platforms to set up for this integration
PLATFORMS = ["sensor", "switch", "binary_sensor", "number"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await _async_register_services(hass)
    _LOGGER.debug("Plum Ecovent async_setup finished")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Setting up Plum Ecovent entry: %s", entry.title)

    entry_data = dict(entry.data)
    entry_options = dict(getattr(entry, "options", {}) or {})
    config = {**entry_data, **entry_options}
    manager = ModbusClientManager(hass, config)
    connected = await manager.async_connect()
    if not connected:
        _LOGGER.error("Failed to connect Modbus for entry %s", entry.entry_id)
        return False

    refreshed_data = await _async_refresh_device_identity_once(hass, entry, manager, entry_data)
    if refreshed_data is not None:
        entry_data = refreshed_data
        config = {**entry_data, **entry_options}

    registers = await async_get_registers_module(hass)
    discovered_definitions = await _async_discover_definitions(manager, registers, config)
    discovered_entities = {
        platform_name: [registers.entity_definition_id(platform_name, definition) for definition in definitions]
        for platform_name, definitions in discovered_definitions.items()
    }

    update_rate = int(config.get(CONF_UPDATE_RATE, DEFAULT_UPDATE_RATE))
    coordinator = PlumEcoventCoordinator(
        hass,
        manager,
        [
            *discovered_definitions["sensor"],
            *discovered_definitions["binary_sensor"],
            *discovered_definitions["switch"],
            *discovered_definitions["number"],
        ],
        update_rate,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:  # pragma: no cover
        _LOGGER.exception("Initial data refresh failed")
        await manager.async_close()
        return False

    runtime_data = {
        "manager": manager,
        "coordinator": coordinator,
        "definitions": discovered_definitions,
        "discovered_entities": discovered_entities,
        "register_support": {
            "available": list(config.get(CONF_AVAILABLE_REGISTERS, config.get(CONF_RESPONDING_REGISTERS, [])) or []),
            "non_responding": list(config.get(CONF_NON_RESPONDING_REGISTERS, []) or []),
            "unsupported": list(config.get(CONF_UNSUPPORTED_REGISTERS, []) or []),
        },
        "device_info": _build_device_info(entry, config),
    }
    entry.runtime_data = runtime_data
    hass.data[DOMAIN][entry.entry_id] = runtime_data

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    # ensure a device entry exists so all entities are grouped
    try:
        from homeassistant.helpers import device_registry as dr

        device_registry = dr.async_get(hass)
        # async_get returns the registry object directly (not a coroutine)
        if hasattr(device_registry, "async_get_or_create"):
            device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={(DOMAIN, entry.entry_id)},
                name=entry.title,
                manufacturer="Plum",
                model=str(config.get(CONF_DEVICE_NAME) or "Ecovent"),
                serial_number=config.get(CONF_DEVICE_SERIAL),
                sw_version=config.get(CONF_FIRMWARE_VERSION),
            )
    except Exception:  # pragma: no cover - very unlikely failure
        _LOGGER.exception("Unable to create device registry entry")

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Plum Ecovent entry: %s", entry.title)
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    entry_data = getattr(entry, "runtime_data", None) or hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data:
        manager: ModbusClientManager | None = entry_data.get("manager")
        if manager:
            await manager.async_close()

    with_logging_map = hass.data.get(DOMAIN, {})
    if isinstance(with_logging_map, dict):
        with_logging_map.pop(entry.entry_id, None)

    if not _loaded_runtime_entries(hass) and hass.services.has_service(DOMAIN, "set_device_setting"):
        hass.services.async_remove(DOMAIN, "set_device_setting")

    return unload_ok


async def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "set_device_setting"):
        return

    from .registers import device_setting_catalog

    catalog = device_setting_catalog()

    async def _async_set_device_setting(call):
        entry_id = call.data.get("entry_id")
        setting = call.data["setting"]
        value = int(call.data["value"])

        setting_meta = catalog.get(setting)
        if setting_meta is None:
            raise ValueError(f"Unknown setting key: {setting}")

        address = int(setting_meta["address"])
        min_value = setting_meta.get("min")
        max_value = setting_meta.get("max")
        if min_value is not None and value < int(min_value):
            raise ValueError(f"Value below minimum {min_value}")
        if max_value is not None and value > int(max_value):
            raise ValueError(f"Value above maximum {max_value}")

        entries = _loaded_runtime_entries(hass)
        if entry_id:
            selected = entries.get(entry_id)
            if selected is None:
                raise ValueError(f"Entry not loaded: {entry_id}")
        else:
            if len(entries) != 1:
                raise ValueError("Provide entry_id when multiple Plum Ecovent entries are loaded")
            selected = next(iter(entries.values()))

        manager: ModbusClientManager | None = selected.get("manager")
        coordinator: PlumEcoventCoordinator | None = selected.get("coordinator")
        if manager is None:
            raise ValueError("Modbus manager is not available")

        success = await manager.write_register(address, value)
        if not success:
            raise ValueError(f"Failed to write register {address}")

        if coordinator is not None:
            await coordinator.async_request_refresh()

    service_schema = vol.Schema(
        {
            vol.Optional("entry_id"): str,
            vol.Required("setting"): vol.In({key: value["name"] for key, value in catalog.items()}),
            vol.Required("value"): vol.Coerce(int),
        }
    )
    hass.services.async_register(DOMAIN, "set_device_setting", _async_set_device_setting, schema=service_schema)


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


def _loaded_runtime_entries(hass: HomeAssistant) -> dict[str, dict[str, Any]]:
    """Return loaded Plum runtime payloads indexed by entry_id.

    Prefer ConfigEntry.runtime_data, with legacy fallback to hass.data storage.
    """
    loaded: dict[str, dict[str, Any]] = {}

    config_entries = getattr(hass, "config_entries", None)
    async_entries = getattr(config_entries, "async_entries", None)
    if callable(async_entries):
        try:
            for entry in async_entries(DOMAIN):
                runtime_data = getattr(entry, "runtime_data", None)
                if isinstance(runtime_data, dict):
                    loaded[entry.entry_id] = runtime_data
        except Exception:
            _LOGGER.debug("Unable to iterate config entries for runtime data", exc_info=True)

    if loaded:
        return loaded

    fallback = hass.data.get(DOMAIN, {})
    if isinstance(fallback, dict):
        for entry_id, payload in fallback.items():
            if isinstance(payload, dict):
                loaded[str(entry_id)] = payload
    return loaded


async def _async_discover_definitions(
    manager: ModbusClientManager, registers_module, config: dict[str, Any]
) -> dict[str, list[Any]]:
    """Discover entities using probed responding registers and user overrides."""
    by_platform: dict[str, list[Any]] = {
        "sensor": list(registers_module.SENSORS),
        "binary_sensor": list(registers_module.BINARY_SENSORS),
        "switch": list(registers_module.SWITCHES),
        "number": list(registers_module.NUMBERS),
    }

    discovered: dict[str, list[Any]] = {}
    has_available_snapshot = (
        CONF_AVAILABLE_REGISTERS in config
        or CONF_RESPONDING_REGISTERS in config
    )
    responding_config = config.get(CONF_AVAILABLE_REGISTERS, config.get(CONF_RESPONDING_REGISTERS, [])) or []
    responding_registers: set[int] = set()
    for value in responding_config:
        try:
            responding_registers.add(int(value))
        except (TypeError, ValueError):
            continue

    availability_cache: dict[int, bool] = {}
    forced_entities = set(config.get(CONF_OPTIONAL_FORCE_ENABLE, []) or [])
    disabled_entities = set(config.get(CONF_OPTIONAL_DISABLE, []) or [])
    if forced_entities & disabled_entities:
        _LOGGER.warning(
            "Entity override conflict detected; disable takes precedence for: %s",
            sorted(forced_entities & disabled_entities),
        )

    has_probe_snapshot = has_available_snapshot

    for platform_name, definitions in by_platform.items():
        entity_definition_id = getattr(registers_module, "entity_definition_id")
        selected: list[Any] = []
        included_entities: list[str] = []
        skipped_entities: list[str] = []
        for definition in definitions:
            entity_id = entity_definition_id(platform_name, definition)
            address = int(getattr(definition, "address", -1))

            if entity_id in disabled_entities:
                skipped_entities.append(entity_id)
                _LOGGER.info(
                    "Skipping %s entity '%s' due to manual disable override",
                    platform_name,
                    getattr(definition, "name", "unknown"),
                )
                continue

            if entity_id in forced_entities:
                selected.append(definition)
                included_entities.append(entity_id)
                continue

            if has_probe_snapshot:
                is_reachable = address in responding_registers
            else:
                is_reachable = availability_cache.get(address)
                if is_reachable is None:
                    response = await manager.read_holding_registers(address, 1)
                    is_reachable = bool(response is not None and hasattr(response, "registers"))
                    availability_cache[address] = is_reachable

            if is_reachable:
                selected.append(definition)
                included_entities.append(entity_id)
            else:
                skipped_entities.append(entity_id)
                _LOGGER.info(
                    "Skipping %s entity '%s' (register %s not reachable)",
                    platform_name,
                    getattr(definition, "name", "unknown"),
                    address,
                )

        discovered[platform_name] = selected
        _LOGGER.info(
            "Entity discovery for %s: selected=%s skipped=%s total_enabled=%s",
            platform_name,
            len(included_entities),
            len(skipped_entities),
            len(selected),
        )
        if included_entities:
            _LOGGER.debug("Included %s entities: %s", platform_name, included_entities)
        if skipped_entities:
            _LOGGER.debug("Skipped %s entities: %s", platform_name, skipped_entities)

    _LOGGER.info(
        "Entity discovery complete: sensor=%s binary_sensor=%s switch=%s number=%s",
        len(discovered.get("sensor", [])),
        len(discovered.get("binary_sensor", [])),
        len(discovered.get("switch", [])),
        len(discovered.get("number", [])),
    )

    return discovered


async def _async_read_device_identity(manager: ModbusClientManager) -> dict[str, str]:
    """Read static identity registers from device."""
    result: dict[str, str] = {}

    firmware_response = await manager.read_holding_registers(16, 1)
    if firmware_response is not None and hasattr(firmware_response, "registers") and firmware_response.registers:
        firmware = format_firmware(firmware_response.registers[0])
        if firmware:
            result[CONF_FIRMWARE_VERSION] = firmware

    name_response = await manager.read_holding_registers(17, 8)
    if name_response is not None and hasattr(name_response, "registers") and name_response.registers:
        device_name = decode_utf8_registers(list(name_response.registers))
        if device_name:
            result[CONF_DEVICE_NAME] = device_name

    serial_response = await manager.read_holding_registers(25, 5)
    if serial_response is not None and hasattr(serial_response, "registers") and serial_response.registers:
        serial = decode_utf8_registers(list(serial_response.registers))
        if serial:
            result[CONF_DEVICE_SERIAL] = serial

    return result


def _build_device_info(entry: ConfigEntry, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": entry.title,
        "manufacturer": "Plum",
        "model": str(config.get(CONF_DEVICE_NAME) or "Ecovent"),
        "serial_number": config.get(CONF_DEVICE_SERIAL),
        "sw_version": config.get(CONF_FIRMWARE_VERSION),
    }


async def _async_refresh_device_identity_once(
    hass: HomeAssistant,
    entry: ConfigEntry,
    manager: ModbusClientManager,
    entry_data: dict[str, Any],
) -> dict[str, Any] | None:
    """Fetch identity at most once after setup when needed.

    This handles:
    - pre-feature entries that don't have stored identity fields yet,
    - entries where config-flow read failed and requested one retry.
    """
    has_identity = all(
        bool(entry_data.get(key))
        for key in (CONF_DEVICE_NAME, CONF_DEVICE_SERIAL, CONF_FIRMWARE_VERSION)
    )
    pending_retry = bool(entry_data.get(CONF_DEVICE_INFO_PENDING_FETCH, False))
    attempted = bool(entry_data.get(CONF_DEVICE_INFO_FETCH_ATTEMPTED, False))

    should_attempt = (pending_retry or not has_identity) and not attempted
    if not should_attempt:
        return None

    identity = await _async_read_device_identity(manager)
    new_data = dict(entry_data)
    new_data.update(identity)
    new_data[CONF_DEVICE_INFO_PENDING_FETCH] = False
    new_data[CONF_DEVICE_INFO_FETCH_ATTEMPTED] = True

    if new_data != entry_data:
        if hasattr(hass, "config_entries") and hasattr(hass.config_entries, "async_update_entry"):
            hass.config_entries.async_update_entry(entry, data=new_data)
        return new_data
    return None
