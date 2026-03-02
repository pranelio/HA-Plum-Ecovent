"""Config flow for Plum Ecovent integration.

Asks for Modbus TCP host, port and unit address.  RTU/serial support has
been removed; only TCP is supported.
"""
from __future__ import annotations

import logging
import asyncio
import contextlib
import socket

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_HOST
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_UNIT,
    CONF_UPDATE_RATE,
    DEFAULT_UPDATE_RATE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_OPTIONAL_DISABLE,
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
                    vol.Required(CONF_HOST, default=""): str,
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
        if unit is None or not (1 <= unit <= 247):
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
            connection_error = await _async_test_connection(host, port)
            if connection_error is not None:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._schema,
                    errors={"base": connection_error},
                )

        title = self._data.get(CONF_NAME, "Plum Ecovent")
        return self.async_create_entry(title=title, data=self._data)

class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            errors: dict[str, str] = {}

            host = user_input.get(CONF_HOST)
            port = user_input.get(CONF_PORT)
            rate = user_input.get(CONF_UPDATE_RATE)
            if rate is None or not (1 <= rate <= 3600):
                errors[CONF_UPDATE_RATE] = "invalid_update_rate"
            unit = user_input.get(CONF_UNIT)
            if unit is None or not (1 <= unit <= 247):
                errors[CONF_UNIT] = "invalid_unit"
            if port is None or not (1 <= port <= 65535):
                errors[CONF_PORT] = "invalid_port"

            forced = set(user_input.get(CONF_OPTIONAL_FORCE_ENABLE, []))
            disabled = set(user_input.get(CONF_OPTIONAL_DISABLE, []))
            if forced & disabled:
                errors["base"] = "overlapping_optional_overrides"

            if not errors and host and port is not None:
                connection_error = await _async_test_connection(host, int(port))
                if connection_error is not None:
                    errors["base"] = connection_error

            if errors:
                return self.async_show_form(step_id="init", data_schema=self._schema(user_input), errors=errors)

            choices = self._optional_choices()
            unknown_forced = [
                value
                for value in self._entry.options.get(CONF_OPTIONAL_FORCE_ENABLE, [])
                if value not in choices
            ]
            unknown_disabled = [
                value
                for value in self._entry.options.get(CONF_OPTIONAL_DISABLE, [])
                if value not in choices
            ]

            user_input[CONF_OPTIONAL_FORCE_ENABLE] = sorted(
                set(user_input.get(CONF_OPTIONAL_FORCE_ENABLE, [])) | set(unknown_forced)
            )
            user_input[CONF_OPTIONAL_DISABLE] = sorted(
                set(user_input.get(CONF_OPTIONAL_DISABLE, [])) | set(unknown_disabled)
            )

            return self.async_create_entry(title="Options", data=user_input)

        current = {**self._entry.data, **self._entry.options}
        return self.async_show_form(step_id="init", data_schema=self._schema(current))

    def _optional_choices(self) -> dict[str, str]:
        from .registers import optional_entity_catalog

        return optional_entity_catalog()

    def _schema(self, current: dict):
        choices = self._optional_choices()
        default_forced = [
            value for value in current.get(CONF_OPTIONAL_FORCE_ENABLE, []) if value in choices
        ]
        default_disabled = [
            value for value in current.get(CONF_OPTIONAL_DISABLE, []) if value in choices
        ]

        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=current.get(CONF_PORT, 502)): vol.All(vol.Coerce(int)),
                vol.Required(CONF_NAME, default=current.get(CONF_NAME, "Plum Ecovent")): str,
                vol.Required(CONF_UPDATE_RATE, default=current.get(CONF_UPDATE_RATE, DEFAULT_UPDATE_RATE)): vol.All(vol.Coerce(int)),
                vol.Required(CONF_UNIT, default=current.get(CONF_UNIT, 1)): vol.All(vol.Coerce(int)),
                vol.Optional(CONF_OPTIONAL_FORCE_ENABLE, default=default_forced): cv.multi_select(choices),
                vol.Optional(CONF_OPTIONAL_DISABLE, default=default_disabled): cv.multi_select(choices),
            }
        )


async def async_get_options_flow(entry: config_entries.ConfigEntry):
    return OptionsFlowHandler(entry)


async def _async_test_connection(host: str, port: int, timeout: float = 5.0) -> str | None:
    try:
        fut = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        return None
    except asyncio.TimeoutError:
        return "connection_timeout"
    except ConnectionRefusedError:
        return "connection_refused"
    except socket.gaierror:
        return "invalid_host"
    except OSError:
        return "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error while validating device reachability")
        return "cannot_connect"

