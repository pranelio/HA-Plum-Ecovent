"""Config flow for Plum Ecovent integration.

Asks for Modbus TCP host, port and unit address.  RTU/serial support has
been removed; only TCP is supported.
"""
from __future__ import annotations

import logging
import asyncio
import contextlib

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_HOST

from .const import (
    DOMAIN,
    CONF_UNIT,
    CONF_UPDATE_RATE,
    DEFAULT_UPDATE_RATE,
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
                    vol.Required(CONF_UPDATE_RATE, default=DEFAULT_UPDATE_RATE): vol.All(vol.Coerce(int)),
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
        update_rate = self._data.get(CONF_UPDATE_RATE)
        if update_rate is None or not (1 <= update_rate <= 3600):
            errors[CONF_UPDATE_RATE] = "invalid_update_rate"
        if errors:
            # re-display the same schema we stored earlier
            return self.async_show_form(step_id="user", data_schema=self._schema, errors=errors)

        # unique id based on host/port
        host = self._data.get(CONF_HOST)
        if host and port is not None:
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

        if host:
            ok = await self._async_test_connection(host, port)
            if not ok:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._schema,
                    errors={"base": "cannot_connect"},
                )

        title = self._data.get(CONF_NAME, "Plum Ecovent")
        return self.async_create_entry(title=title, data=self._data)

    async def _async_test_connection(self, host: str, port: int, timeout: float = 5.0) -> bool:
        try:
            fut = asyncio.open_connection(host, port)
            reader, writer = await asyncio.wait_for(fut, timeout=timeout)
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            return True
        except Exception:
            return False


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            errors: dict[str, str] = {}
            rate = user_input.get(CONF_UPDATE_RATE)
            if rate is None or not (1 <= rate <= 3600):
                errors[CONF_UPDATE_RATE] = "invalid_update_rate"
            unit = user_input.get(CONF_UNIT)
            if unit is None or not (1 <= unit <= 255):
                errors[CONF_UNIT] = "invalid_unit"
            if errors:
                return self.async_show_form(step_id="init", data_schema=self._schema(user_input), errors=errors)
            return self.async_create_entry(title="Options", data=user_input)

        current = {**self._entry.data, **self._entry.options}
        return self.async_show_form(step_id="init", data_schema=self._schema(current))

    def _schema(self, current: dict):
        return vol.Schema(
            {
                vol.Required(CONF_UPDATE_RATE, default=current.get(CONF_UPDATE_RATE, DEFAULT_UPDATE_RATE)): vol.All(vol.Coerce(int)),
                vol.Required(CONF_UNIT, default=current.get(CONF_UNIT, 1)): vol.All(vol.Coerce(int)),
            }
        )


async def async_get_options_flow(entry: config_entries.ConfigEntry):
    return OptionsFlowHandler(entry)

