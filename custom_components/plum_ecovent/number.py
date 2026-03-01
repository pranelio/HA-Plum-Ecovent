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

from .const import DOMAIN
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    manager: ModbusClientManager = hass.data[DOMAIN][entry.entry_id]
    from .registers import NUMBERS

    entities = []
    for definition in NUMBERS:
        entities.append(PlumEcoventNumber(manager, entry, definition))
    async_add_entities(entities, True)


class PlumEcoventNumber(NumberEntity):
    """Number entity representing a register."""

    def __init__(
        self, manager: ModbusClientManager, entry: ConfigEntry, definition
    ) -> None:
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_native_value = 0
        if definition.unit_of_measurement:
            self._attr_native_unit_of_measurement = definition.unit_of_measurement
        if definition.device_class:
            self._attr_device_class = definition.device_class
        if definition.entity_category:
            self._attr_entity_category = definition.entity_category
        if definition.step is not None:
            self._attr_native_step = definition.step
        if definition.min_value is not None:
            self._attr_native_min_value = definition.min_value
        if definition.max_value is not None:
            self._attr_native_max_value = definition.max_value

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
            self._attr_native_value = result.registers[0]
        else:
            self._attr_native_value = 0

    async def async_set_native_value(self, value: float) -> None:
        await self._manager.write_register(self._definition.address, int(value))
        self._attr_native_value = value

