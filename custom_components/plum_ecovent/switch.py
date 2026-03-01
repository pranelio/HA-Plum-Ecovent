"""Switch platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.switch import SwitchEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except Exception:  # Running outside Home Assistant for tests
    class SwitchEntity:  # type: ignore
        pass

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN, REG_SWITCH
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: ModbusClientManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PlumEcoventSwitch(manager, entry)], True)


class PlumEcoventSwitch(SwitchEntity):
    """Simple switch that writes a register on the device."""

    def __init__(self, manager: ModbusClientManager, entry: ConfigEntry) -> None:
        self._manager = manager
        self._entry = entry
        self._attr_name = f"{entry.title} Switch"
        self._attr_is_on = False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    async def async_update(self) -> None:
        result = await self._manager.read_holding_registers(REG_SWITCH, 1)
        if result and hasattr(result, "registers"):
            self._attr_is_on = bool(result.registers[0])
        else:
            self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self._manager.write_register(REG_SWITCH, 1)
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        await self._manager.write_register(REG_SWITCH, 0)
        self._attr_is_on = False
