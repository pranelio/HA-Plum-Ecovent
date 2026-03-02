"""Plum Ecovent integration entry point.

Minimal async setup and setup_entry placeholders.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    CONF_UPDATE_RATE,
    DEFAULT_UPDATE_RATE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_OPTIONAL_DISABLE,
)
from .modbus_client import ModbusClientManager
from .coordinator import PlumEcoventCoordinator

# Platforms to set up for this integration
PLATFORMS = ["sensor", "switch", "binary_sensor", "number"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Plum Ecovent async_setup finished")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Setting up Plum Ecovent entry: %s", entry.title)

    config = {**entry.data, **entry.options}
    manager = ModbusClientManager(hass, config)
    connected = await manager.async_connect()
    if not connected:
        _LOGGER.error("Failed to connect Modbus for entry %s", entry.entry_id)
        return False

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
                model="Ecovent",
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

    return unload_ok


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
