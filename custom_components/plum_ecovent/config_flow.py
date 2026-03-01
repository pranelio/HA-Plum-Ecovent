"""Config flow for Plum Ecovent integration.

This flow lets the user choose between Modbus TCP and Modbus RTU (serial)
and captures the relevant connection settings.
"""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_HOST

from .const import (
    DOMAIN,
    CONF_MODBUS_TYPE,
    MODBUS_TYPE_TCP,
    MODBUS_TYPE_RTU,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_MODBUS_TYPE, default=MODBUS_TYPE_TCP): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Plum Ecovent."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        self._data.update(user_input)
        return await self.async_step_modbus_settings()

    async def async_step_modbus_settings(self, user_input=None):
        """Collect the Modbus connection settings based on chosen type."""
        if self._data.get(CONF_MODBUS_TYPE) == MODBUS_TYPE_TCP:
            schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default="127.0.0.1"): str,
                    vol.Required(CONF_PORT, default=502): int,
                    vol.Optional(CONF_NAME, default="Plum Ecovent"): str,
                }
            )
            step_id = "modbus_tcp"
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_SERIAL_PORT, default="/dev/ttyUSB0"): str,
                    vol.Required(CONF_BAUDRATE, default=9600): int,
                    vol.Optional(CONF_NAME, default="Plum Ecovent"): str,
                }
            )
            step_id = "modbus_rtu"

        if user_input is None:
            return self.async_show_form(step_id=step_id, data_schema=schema)

        self._data.update(user_input)

        title = self._data.get(CONF_NAME, "Plum Ecovent")
        return self.async_create_entry(title=title, data=self._data)
