"""Plum Ecovent integration entry point.

Minimal async setup and setup_entry placeholders.
"""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
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

    manager = ModbusClientManager(hass, entry.data)
    connected = await manager.async_connect()
    if not connected:
        _LOGGER.error("Failed to connect Modbus for entry %s", entry.entry_id)
        return False

    from . import registers

    coordinator = PlumEcoventCoordinator(
        hass,
        manager,
        [
            *registers.SENSORS,
            *registers.BINARY_SENSORS,
            *registers.SWITCHES,
            *registers.NUMBERS,
        ],
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
    }

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
