"""Switch platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.switch import SwitchEntity
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.exceptions import HomeAssistantError
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

    class HomeAssistantError(Exception):
        pass

    from typing import Any as AddEntitiesCallback  # type: ignore

from .const import DOMAIN
from .coordinator import build_definition_key
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = getattr(entry, "runtime_data", None)
    if not isinstance(entry_data, dict):
        entry_data = hass.data[DOMAIN][entry.entry_id]
    manager: ModbusClientManager = entry_data["manager"]
    coordinator = entry_data["coordinator"]
    device_info = entry_data.get("device_info")
    discovered = entry_data.get("definitions", {})
    switches = discovered.get("switch", [])
    if "switch" not in discovered:
        _LOGGER.warning("No discovered switch definitions found for entry %s; no switches will be created", entry.entry_id)

    entities = []
    for definition in switches:
        entities.append(PlumEcoventSwitch(manager, coordinator, entry, definition, device_info=device_info))
    async_add_entities(entities, True)


class PlumEcoventSwitch(CoordinatorEntity, SwitchEntity):
    """Switch representing a Modbus coil/bitmask."""

    _attr_has_entity_name = True

    def __init__(
        self, manager: ModbusClientManager, coordinator, entry: ConfigEntry, definition, device_info=None
    ) -> None:
        super().__init__(coordinator)
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._key = build_definition_key(definition)
        name_slug = (getattr(definition, "key", None) or definition.name).replace(" ", "_").lower()
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_unique_id = f"{entry.entry_id}_switch_{definition.address}_{name_slug}"
        self._attr_is_on = False
        self._device_info = device_info or {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }
        if definition.entity_category is not None:
            try:
                self._attr_entity_category = EntityCategory(definition.entity_category)
            except Exception:
                self._attr_entity_category = None

    @property
    def device_info(self):
        return self._device_info

    async def async_update(self) -> None:
        if self.coordinator and self.coordinator.update_interval is None:
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

    async def _async_set_bit_state(self, turn_on: bool) -> bool:
        current_register_value = 0
        response = await self._manager.read_holding_registers(self._definition.address, 1)
        if response is not None and hasattr(response, "registers") and response.registers:
            current_register_value = int(response.registers[0])

        if turn_on:
            new_register_value = current_register_value | self._definition.bitmask
        else:
            new_register_value = current_register_value & ~self._definition.bitmask

        success = await self._manager.write_register(self._definition.address, int(new_register_value))
        if success and self.coordinator:
            await self.coordinator.async_request_refresh()
        return bool(success)

    async def async_turn_on(self, **kwargs) -> None:
        success = await self._async_set_bit_state(True)
        if not success:
            raise HomeAssistantError(f"Failed to write register {self._definition.address}")

    async def async_turn_off(self, **kwargs) -> None:
        success = await self._async_set_bit_state(False)
        if not success:
            raise HomeAssistantError(f"Failed to write register {self._definition.address}")

