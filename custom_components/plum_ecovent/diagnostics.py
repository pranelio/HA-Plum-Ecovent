"""Diagnostics support for Plum Ecovent integration."""
from __future__ import annotations

try:
    from homeassistant.components.diagnostics import async_redact_data  # type: ignore[import-not-found]
    from homeassistant.config_entries import ConfigEntry  # type: ignore[import-not-found]
    from homeassistant.core import HomeAssistant  # type: ignore[import-not-found]
except Exception:  # Running outside Home Assistant for tests
    class ConfigEntry:  # type: ignore
        pass

    class HomeAssistant:  # type: ignore
        pass

    def async_redact_data(data: dict, _to_redact: set[str]) -> dict:  # type: ignore
        return data

from .const import DOMAIN, CONF_HOST

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get("coordinator")
    manager = entry_data.get("manager")

    diagnostics = {
        "entry": {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "runtime": {
            "coordinator_present": coordinator is not None,
            "manager_present": manager is not None,
            "last_update_success": getattr(coordinator, "last_update_success", None),
            "tracked_values": len(getattr(coordinator, "data", {}) or {}),
            "modbus_unit": getattr(manager, "unit", None),
            "retries": getattr(manager, "retries", None),
            "timeout": getattr(manager, "timeout", None),
        },
    }

    return async_redact_data(diagnostics, TO_REDACT)
