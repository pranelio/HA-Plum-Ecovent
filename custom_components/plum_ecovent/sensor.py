"""Sensor platform for Plum Ecovent integration."""
from __future__ import annotations

import logging

try:
    from homeassistant.components.sensor import SensorEntity, SensorStateClass
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.update_coordinator import CoordinatorEntity
    from homeassistant.const import EntityCategory
except Exception:  # Running outside Home Assistant for tests
    class SensorEntity:  # type: ignore
        pass

    class SensorStateClass:  # type: ignore
        MEASUREMENT = None

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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]
    manager: ModbusClientManager = entry_data["manager"]
    coordinator = entry_data["coordinator"]
    device_info = entry_data.get("device_info")
    discovered = entry_data.get("definitions", {})
    sensors = discovered.get("sensor", [])
    if "sensor" not in discovered:
        _LOGGER.warning("No discovered sensor definitions found for entry %s; no sensors will be created", entry.entry_id)

    entities = [PlumEcoventSensor(manager, coordinator, entry, d, idx, device_info=device_info) for idx, d in enumerate(sensors)]
    entities.append(PlumEcoventRetryCounterSensor(manager, coordinator, entry, device_info=device_info))
    async_add_entities(entities, True)


class PlumEcoventSensor(CoordinatorEntity, SensorEntity):
    """Sensor reading a specific register defined in `registers.SENSORS`."""

    def __init__(
        self, manager: ModbusClientManager, coordinator, entry: ConfigEntry, definition, idx: int = 0, device_info=None
    ) -> None:
        super().__init__(coordinator)
        self._manager = manager
        self._entry = entry
        self._definition = definition
        self._key = build_definition_key(definition)
        name_slug = definition.name.replace(" ", "_").lower()
        self._attr_name = f"{entry.title} {definition.name}"
        self._attr_unique_id = f"{entry.entry_id}_sensor_{definition.address}_{name_slug}_{idx}"
        self._state = None
        self._device_info = device_info or {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }
        if definition.device_class:
            self._attr_device_class = definition.device_class
        if definition.unit_of_measurement:
            self._attr_native_unit_of_measurement = definition.unit_of_measurement
        if definition.accuracy_decimals is not None:
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if definition.entity_category:
            try:
                self._attr_entity_category = EntityCategory(definition.entity_category)
            except Exception:
                self._attr_entity_category = None

    @property
    def device_info(self):
        return self._device_info

    @property
    def native_value(self):
        value = None
        if self.coordinator and self.coordinator.data is not None:
            value = self.coordinator.data.get(self._key)
        self._attr_available = value is not None
        self._state = value
        return value

    async def async_update(self) -> None:
        # Respect coordinator schedule; only force refresh if no interval set
        if self.coordinator and self.coordinator.update_interval is None:
            await self.coordinator.async_request_refresh()


class PlumEcoventRetryCounterSensor(CoordinatorEntity, SensorEntity):
    """Diagnostic sensor exposing total Modbus retry attempts."""

    def __init__(self, manager: ModbusClientManager, coordinator, entry: ConfigEntry, device_info=None) -> None:
        super().__init__(coordinator)
        self._manager = manager
        self._entry = entry
        self._attr_name = f"{entry.title} Communication Retries"
        self._attr_unique_id = f"{entry.entry_id}_diagnostic_comm_retries"
        self._attr_icon = "mdi:counter"
        try:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        except Exception:
            self._attr_entity_category = "diagnostic"
        if hasattr(SensorStateClass, "TOTAL_INCREASING"):
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._device_info = device_info or {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": "Plum",
            "model": "Ecovent",
        }

    @property
    def device_info(self):
        return self._device_info

    @property
    def native_value(self):
        return int(getattr(self._manager, "retry_counter", 0))

