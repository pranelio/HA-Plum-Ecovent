"""Number platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.number import NumberEntity, NumberMode
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    from homeassistant.const import EntityCategory
except Exception:  # Running outside Home Assistant for tests
    class NumberEntity:  # type: ignore
        pass

    class NumberMode:  # type: ignore
        BOX = "box"
        AUTO = "auto"
        SLIDER = "slider"

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
    device_info = entry_data.get("device_info")
    discovered = entry_data.get("definitions", {})
    numbers = discovered.get("number", [])
    if "number" not in discovered:
        _LOGGER.warning("No discovered number definitions found for entry %s; no numbers will be created", entry.entry_id)

    entities = []
    for definition in numbers:
        entities.append(PlumEcoventNumber(manager, coordinator, entry, definition, device_info=device_info))
    async_add_entities(entities, True)


class PlumEcoventNumber(CoordinatorEntity, NumberEntity):
    """Number entity representing a register."""

    def __init__(
        self, manager: ModbusClientManager, coordinator, entry: ConfigEntry, definition, device_info=None
    ) -> None:
        super().__init__(coordinator)
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._key = build_definition_key(definition)
        name_slug = definition.name.replace(" ", "_").lower()
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_unique_id = f"{entry.entry_id}_number_{definition.address}_{name_slug}"
        self._attr_native_value = 0
        self._device_info = device_info or {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }
        if definition.unit_of_measurement:
            self._attr_native_unit_of_measurement = definition.unit_of_measurement
        if definition.device_class:
            self._attr_device_class = definition.device_class
        if definition.entity_category:
            try:
                self._attr_entity_category = EntityCategory(definition.entity_category)
            except Exception:
                self._attr_entity_category = None
        if definition.step is not None:
            self._attr_native_step = definition.step
        if definition.min_value is not None:
            self._attr_native_min_value = definition.min_value
        if definition.max_value is not None:
            self._attr_native_max_value = definition.max_value
        if definition.mode is not None:
            mode = definition.mode
            if isinstance(mode, str):
                mode = mode.lower()
                if hasattr(NumberMode, "BOX") and mode == "box":
                    mode = NumberMode.BOX
                elif hasattr(NumberMode, "AUTO") and mode == "auto":
                    mode = NumberMode.AUTO
                elif hasattr(NumberMode, "SLIDER") and mode == "slider":
                    mode = NumberMode.SLIDER
            self._attr_mode = mode

    @property
    def device_info(self):
        return self._device_info

    async def async_update(self) -> None:
        if self.coordinator and self.coordinator.update_interval is None:
            await self.coordinator.async_request_refresh()

    async def async_set_native_value(self, value: float) -> None:
        await self._manager.write_register(self._definition.address, int(value))
        self._attr_native_value = value

    @property
    def native_value(self):
        value = None
        if self.coordinator and self.coordinator.data is not None:
            value = self.coordinator.data.get(self._key)
        self._attr_available = value is not None
        return value if value is not None else self._attr_native_value

