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
    DOMAIN,
    CONF_UPDATE_RATE,
    DEFAULT_UPDATE_RATE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_OPTIONAL_DISABLE,
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

    from . import registers
    discovered_definitions = await _async_discover_definitions(manager, registers, config)
    discovered_entities = {
        platform_name: [f"{definition.address}:{definition.name}" for definition in definitions]
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

    hass.data[DOMAIN][entry.entry_id] = {
        "manager": manager,
        "coordinator": coordinator,
        "definitions": discovered_definitions,
        "discovered_entities": discovered_entities,
        "device_info": _build_device_info(entry, config),
    }

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

    entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data:
        manager: ModbusClientManager | None = entry_data.get("manager")
        if manager:
            await manager.async_close()

    if not hass.data.get(DOMAIN) and hass.services.has_service(DOMAIN, "set_device_setting"):
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

        entries = list(hass.data.get(DOMAIN, {}).items())
        if entry_id:
            selected = hass.data.get(DOMAIN, {}).get(entry_id)
            if selected is None:
                raise ValueError(f"Entry not loaded: {entry_id}")
        else:
            if len(entries) != 1:
                raise ValueError("Provide entry_id when multiple Plum Ecovent entries are loaded")
            selected = entries[0][1]

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


async def _async_discover_definitions(
    manager: ModbusClientManager, registers_module, config: dict[str, Any]
) -> dict[str, list[Any]]:
    """Discover model-dependent entities by probing optional registers only."""
    by_platform: dict[str, list[Any]] = {
        "sensor": list(registers_module.SENSORS),
        "binary_sensor": list(registers_module.BINARY_SENSORS),
        "switch": list(registers_module.SWITCHES),
        "number": list(registers_module.NUMBERS),
    }

    discovered: dict[str, list[Any]] = {}
    availability_cache: dict[int, bool] = {}
    forced_optional = set(config.get(CONF_OPTIONAL_FORCE_ENABLE, []) or [])
    disabled_optional = set(config.get(CONF_OPTIONAL_DISABLE, []) or [])
    if forced_optional & disabled_optional:
        _LOGGER.warning(
            "Optional entity override conflict detected; disable takes precedence for: %s",
            sorted(forced_optional & disabled_optional),
        )

    for platform_name, definitions in by_platform.items():
        optional_entity_id = getattr(registers_module, "optional_entity_id")
        selected: list[Any] = []
        required_count = 0
        optional_count = 0
        discovered_optional: list[str] = []
        skipped_optional: list[str] = []
        for definition in definitions:
            if not getattr(definition, "optional", False):
                selected.append(definition)
                required_count += 1
                continue

            optional_count += 1
            entity_id = optional_entity_id(platform_name, definition)

            if entity_id in disabled_optional:
                skipped_optional.append(entity_id)
                _LOGGER.info(
                    "Skipping optional %s entity '%s' due to manual disable override",
                    platform_name,
                    getattr(definition, "name", "unknown"),
                )
                continue

            if entity_id in forced_optional:
                selected.append(definition)
                discovered_optional.append(entity_id)
                continue

            address = int(getattr(definition, "address", -1))
            is_reachable = availability_cache.get(address)
            if is_reachable is None:
                response = await manager.read_holding_registers(address, 1)
                is_reachable = bool(response is not None and hasattr(response, "registers"))
                availability_cache[address] = is_reachable

            if is_reachable:
                selected.append(definition)
                discovered_optional.append(entity_id)
            else:
                skipped_optional.append(entity_id)
                _LOGGER.info(
                    "Skipping optional %s entity '%s' (register %s not reachable)",
                    platform_name,
                    getattr(definition, "name", "unknown"),
                    address,
                )

        discovered[platform_name] = selected
        _LOGGER.info(
            "Entity discovery for %s: required=%s optional=%s discovered_optional=%s total_enabled=%s",
            platform_name,
            required_count,
            optional_count,
            len(discovered_optional),
            len(selected),
        )
        if discovered_optional:
            _LOGGER.debug("Discovered optional %s entities: %s", platform_name, discovered_optional)
        if skipped_optional:
            _LOGGER.debug("Skipped optional %s entities: %s", platform_name, skipped_optional)

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
