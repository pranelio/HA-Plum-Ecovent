"""Number platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.number import NumberEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except Exception:  # Running outside Home Assistant for tests
    class NumberEntity:  # type: ignore
        pass

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN, REG_NUMBER
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: ModbusClientManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlumEcoventNumber(manager, entry)], True)


class PlumEcoventNumber(NumberEntity):
    """Simple number entity tied to a modbus register."""

    def __init__(self, manager: ModbusClientManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_name = f"{entry.title} Number"
        self._attr_native_value = 0

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    async def async_update(self) -> None:
        result = await self._manager.read_holding_registers(REG_NUMBER, 1)
        if result and hasattr(result, "registers"):
            self._attr_native_value = result.registers[0]
        else:
            self._attr_native_value = 0

    async def async_set_native_value(self, value: float) -> None:
        # write integer part for simplicity
        await self._manager.write_register(REG_NUMBER, int(value))
        self._attr_native_value = value
