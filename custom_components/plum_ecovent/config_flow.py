"""Config flow for Plum Ecovent integration.

Asks for Modbus TCP host, port and unit address.  RTU/serial support has
been removed; only TCP is supported.
"""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_HOST

from .const import (
    DOMAIN,
    CONF_UNIT,
)

_LOGGER = logging.getLogger(__name__)




class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Plum Ecovent."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        """Initial step — ask for TCP parameters."""
        if user_input is None:
            # simple integer inputs; avoid sliders by not using vol.Range
            self._schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default="127.0.0.1"): str,
                    vol.Required(CONF_PORT, default=502): vol.All(vol.Coerce(int)),
                    vol.Required(CONF_UNIT, default=1): vol.All(vol.Coerce(int)),
                    vol.Optional(CONF_NAME, default="Plum Ecovent"): str,
                }
            )
            return self.async_show_form(step_id="user", data_schema=self._schema)

        self._data.update(user_input)

        # ensure integer fields are in valid ranges; report errors if not
        errors: dict[str, str] = {}
        port = self._data.get(CONF_PORT)
        if port is None or not (1 <= port <= 65535):
            errors[CONF_PORT] = "invalid_port"
        unit = self._data.get(CONF_UNIT)
        if unit is None or not (1 <= unit <= 255):
            errors[CONF_UNIT] = "invalid_unit"
        if errors:
            # re-display the same schema we stored earlier
            return self.async_show_form(step_id="user", data_schema=self._schema, errors=errors)

        # unique id based on host/port
        host = self._data.get(CONF_HOST)
        if host and port is not None:
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

        title = self._data.get(CONF_NAME, "Plum Ecovent")
        return self.async_create_entry(title=title, data=self._data)

