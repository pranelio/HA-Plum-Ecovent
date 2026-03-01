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
            schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default="127.0.0.1"): str,
                    vol.Required(CONF_PORT, default=502): int,
                    vol.Required(CONF_UNIT, default=1): vol.All(int, vol.Range(min=1, max=255)),
                    vol.Optional(CONF_NAME, default="Plum Ecovent"): str,
                }
            )
            return self.async_show_form(step_id="user", data_schema=schema)

        self._data.update(user_input)

        # unique id based on host/port
        host = self._data.get(CONF_HOST)
        port = self._data.get(CONF_PORT)
        if host and port is not None:
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

        title = self._data.get(CONF_NAME, "Plum Ecovent")
        return self.async_create_entry(title=title, data=self._data)

