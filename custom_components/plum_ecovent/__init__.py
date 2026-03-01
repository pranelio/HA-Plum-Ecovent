"""Plum Ecovent integration entry point.

Minimal async setup and setup_entry placeholders.
"""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .modbus_client import ModbusClientManager

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

    hass.data[DOMAIN][entry.entry_id] = manager

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Unloading Plum Ecovent entry: %s", entry.title)
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    manager: ModbusClientManager | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if manager:
        await manager.async_close()

    return unload_ok
