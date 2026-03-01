"""Binary sensor platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.binary_sensor import BinarySensorEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
except Exception:  # Running outside Home Assistant for tests
    class BinarySensorEntity:  # type: ignore
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
    from .registers import BINARY_SENSORS

    entities = []
    for definition in BINARY_SENSORS:
        entities.append(PlumEcoventBinarySensor(manager, entry, definition))
    async_add_entities(entities, True)


class PlumEcoventBinarySensor(BinarySensorEntity):
    """Binary sensor that reads a particular Modbus register."""

    def __init__(
        self, manager: ModbusClientManager, entry: ConfigEntry, definition
    ) -> None:
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_is_on = False
        if definition.device_class is not None:
            self._attr_device_class = definition.device_class
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
            self._attr_is_on = bool(result.registers[0])
        else:
            self._attr_is_on = False

