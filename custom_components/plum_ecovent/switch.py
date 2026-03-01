"""Switch platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.switch import SwitchEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    from homeassistant.const import EntityCategory
except Exception:  # Running outside Home Assistant for tests
    class SwitchEntity:  # type: ignore
        pass

    class CoordinatorEntity:  # type: ignore
        def __init__(self, coordinator=None):
            self.coordinator = coordinator

    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN
from .coordinator import build_definition_key
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    manager: ModbusClientManager = entry_data["manager"]
    coordinator = entry_data["coordinator"]
    from .registers import SWITCHES

    entities = []
    for definition in SWITCHES:
        entities.append(PlumEcoventSwitch(manager, coordinator, entry, definition))
    async_add_entities(entities, True)


class PlumEcoventSwitch(CoordinatorEntity, SwitchEntity):
    """Switch representing a Modbus coil/bitmask."""

    def __init__(
        self, manager: ModbusClientManager, coordinator, entry: ConfigEntry, definition
    ) -> None:
        super().__init__(coordinator)
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._key = build_definition_key(definition)
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_unique_id = f"{entry.entry_id}_switch_{definition.address}_{definition.name}"
        self._attr_is_on = False
        if definition.entity_category is not None:
            try:
                self._attr_entity_category = EntityCategory(definition.entity_category)
            except Exception:
                self._attr_entity_category = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    async def async_update(self) -> None:
        if self.coordinator:
            await self.coordinator.async_request_refresh()

    @property
    def is_on(self):
        value = None
        if self.coordinator and self.coordinator.data is not None:
            value = self.coordinator.data.get(self._key)
        self._attr_available = value is not None
        if value is None:
            return False
        return bool(value & self._definition.bitmask)

    async def async_turn_on(self, **kwargs) -> None:
        await self._manager.write_register(
            self._definition.address, self._definition.bitmask
        )
        self._attr_is_on = True

    async def async_turn_off(self, **kwargs) -> None:
        await self._manager.write_register(self._definition.address, 0)
        self._attr_is_on = False

