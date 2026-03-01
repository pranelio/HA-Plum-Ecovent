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

from .const import DOMAIN
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: ModbusClientManager = hass.data[DOMAIN][entry.entry_id]
    from .registers import SWITCHES

    entities = []
    for definition in SWITCHES:
        entities.append(PlumEcoventSwitch(manager, entry, definition))
    async_add_entities(entities, True)


class PlumEcoventSwitch(SwitchEntity):
    """Switch representing a Modbus coil/bitmask."""

    def __init__(
        self, manager: ModbusClientManager, entry: ConfigEntry, definition
    ) -> None:
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_is_on = False
        if definition.entity_category is not None:
            self._attr_entity_category = definition.entity_category

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    async def async_update(self) -> None:
        result = await self._manager.read_holding_registers(
            self._definition.address, 1
        )
        if result and hasattr(result, "registers"):
            value = result.registers[0]
            self._attr_is_on = bool(value & self._definition.bitmask)
        else:
            self._attr_is_on = False

    async def async_turn_on(self, **kwargs) -> None:
        await self._manager.write_register(
            self._definition.address, self._definition.bitmask
        )
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        await self._manager.write_register(self._definition.address, 0)
        self._attr_is_on = False

