"""Coordinator to batch Modbus reads for Plum Ecovent."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Tuple

try:
    from homeassistant.helpers.update_coordinator import (  # type: ignore
        DataUpdateCoordinator,
        UpdateFailed,
    )
except Exception:  # Running outside Home Assistant for tests
    class UpdateFailed(Exception):
        pass

    class DataUpdateCoordinator:  # type: ignore
        def __init__(self, hass=None, logger=None, name=None, update_interval=None):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data: Dict[str, Any] = {}
            self.last_update_success = True

        async def async_config_entry_first_refresh(self):
            self.data = await self._async_update_data()
            return self

        async def async_refresh(self):
            self.data = await self._async_update_data()
            return self

        async def async_request_refresh(self):
            return await self.async_refresh()

        async def _async_update_data(self):  # pragma: no cover - stub
            return {}

_LOGGER = logging.getLogger(__name__)


class PlumEcoventCoordinator(DataUpdateCoordinator):
    """Batch Modbus reads and fan out to entities."""

    def __init__(self, hass, manager, definitions: Iterable[Any]):
        super().__init__(
            hass,
            _LOGGER,
            name="plum_ecovent_data",
            update_interval=None,  # rely on entity polling interval
        )
        self._manager = manager
        self._defs = list(definitions)
        self._cycle = 0

    @staticmethod
    def _key(defn: Any) -> str:
        return f"{defn.__class__.__name__}:{defn.address}:{defn.name}"

    @staticmethod
    def _apply_filters(value: Any, filters: Any) -> Any:
        if not filters:
            return value
        filtered = value
        for item in filters:
            if not isinstance(item, dict):
                continue
            if "multiply" in item:
                try:
                    filtered = filtered * item["multiply"]
                except Exception:
                    continue
        return filtered

    async def _async_update_data(self) -> Dict[str, Any]:
        results: Dict[str, Any] = dict(self.data or {})
        self._cycle += 1
        for definition in self._defs:
            key = self._key(definition)
            skip = getattr(definition, "skip_updates", None)
            if skip and key in results and (self._cycle % skip) != 1:
                continue

            response = await self._manager.read_holding_registers(definition.address, 1)
            if response is None or not hasattr(response, "registers"):
                results[key] = None
                continue

            raw = response.registers[0]
            value = self._apply_filters(raw, getattr(definition, "filters", None))
            results[key] = value
        return results


def build_definition_key(defn: Any) -> str:
    """Helper exported for entities and tests to compute coordinator keys."""
    return PlumEcoventCoordinator._key(defn)
