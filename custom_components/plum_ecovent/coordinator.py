"""Coordinator to batch Modbus reads for Plum Ecovent."""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Tuple
from datetime import timedelta

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

    def __init__(self, hass, manager, definitions: Iterable[Any], update_rate: int):
        super().__init__(
            hass,
            _LOGGER,
            name="plum_ecovent_data",
            update_interval=timedelta(seconds=update_rate),
        )
        self._manager = manager
        self._defs = list(definitions)
        self._cycle = 0

    @staticmethod
    def _key(defn: Any) -> str:
        stable_key = getattr(defn, "key", None) or getattr(defn, "name", "unknown")
        return f"{defn.__class__.__name__}:{defn.address}:{stable_key}"

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
        successful_reads = 0
        failed_reads = 0
        for definition in self._defs:
            key = self._key(definition)
            skip = getattr(definition, "skip_updates", None)
            if skip and key in results and (self._cycle % skip) != 1:
                continue

            response = await self._manager.read_holding_registers(definition.address, 1)
            if response is None or not hasattr(response, "registers"):
                results[key] = None
                failed_reads += 1
                continue

            raw = response.registers[0]
            value = self._apply_filters(raw, getattr(definition, "filters", None))
            results[key] = value
            successful_reads += 1

        if self._defs and successful_reads == 0:
            raise UpdateFailed("All Modbus reads failed")

        if failed_reads:
            _LOGGER.warning(
                "Coordinator update completed with partial failures: %s/%s reads failed",
                failed_reads,
                successful_reads + failed_reads,
            )
        return results


def build_definition_key(defn: Any) -> str:
    """Helper exported for entities and tests to compute coordinator keys."""
    return PlumEcoventCoordinator._key(defn)
