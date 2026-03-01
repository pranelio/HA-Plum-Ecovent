"""Sensor platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.sensor import SensorEntity, SensorStateClass
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except Exception:  # Running outside Home Assistant for tests
    class SensorEntity:  # type: ignore
        pass

    class SensorStateClass:  # type: ignore
        MEASUREMENT = None

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
    from .registers import SENSORS

    entities = [PlumEcoventSensor(manager, entry, d) for d in SENSORS]
    async_add_entities(entities, True)


class PlumEcoventSensor(SensorEntity):
    """Sensor reading a specific register defined in `registers.SENSORS`."""

    def __init__(
        self, manager: ModbusClientManager, entry: ConfigEntry, definition
    ) -> None:
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._attr_name = f"{entry.title} {definition.name}"
        self._state = None
        if definition.device_class:
            self._attr_device_class = definition.device_class
        if definition.unit_of_measurement:
            self._attr_native_unit_of_measurement = definition.unit_of_measurement
        if definition.accuracy_decimals is not None:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if definition.entity_category:
            self._attr_entity_category = definition.entity_category

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    @property
    def native_value(self):
        return self._state

    async def async_update(self) -> None:
        result = await self._manager.read_holding_registers(
            self._definition.address, 1
        )
        if result and hasattr(result, "registers"):
            self._state = result.registers[0]
        else:
            self._state = None

