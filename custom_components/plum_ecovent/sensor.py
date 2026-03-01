"""Sensor platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.sensor import SensorEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except Exception:  # Running outside Home Assistant for tests
    class SensorEntity:  # type: ignore
        pass

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    manager: ModbusClientManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlumEcoventSensor(manager, entry)], True)


class PlumEcoventSensor(SensorEntity):
    """Simple sensor that reads a holding register (address 0) from the device."""

    def __init__(self, manager: ModbusClientManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_name = f"{entry.title} Register 0"
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self) -> None:
        result = await self._manager.read_holding_registers(0, 1)
        if result and hasattr(result, "registers"):
            self._state = result.registers[0]
        else:
            self._state = None
