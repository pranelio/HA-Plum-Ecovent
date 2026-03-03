"""Config flow for Plum Ecovent integration."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import socket
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_DEVICE_INFO_FETCH_ATTEMPTED,
    CONF_DEVICE_INFO_PENDING_FETCH,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SERIAL,
    CONF_DEVICE_SETTINGS_GROUP,
    CONF_DEVICE_SETTINGS_VALUES,
    CONF_FIRMWARE_VERSION,
    CONF_OPTIONS_ACTION,
    CONF_OPTIONAL_DISABLE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_RESPONDING_REGISTERS,
    CONF_UNIT,
    CONF_UPDATE_RATE,
    DEFAULT_UPDATE_RATE,
    DOMAIN,
)
from .device_info import decode_utf8_registers, format_firmware
from .modbus_client import ModbusClientManager

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Plum Ecovent."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._verify_task: asyncio.Task[str | None] | None = None
        self._probe_task: asyncio.Task[tuple[list[int], dict[str, str]]] | None = None
        self._schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=""): str,
                vol.Required(CONF_PORT, default=502): vol.All(vol.Coerce(int)),
                vol.Required(CONF_UNIT, default=1): vol.All(vol.Coerce(int)),
                vol.Required(CONF_UPDATE_RATE, default=DEFAULT_UPDATE_RATE): vol.All(vol.Coerce(int)),
                vol.Optional(CONF_NAME, default="Plum Ecovent"): str,
            }
        )

    async def async_step_user(self, user_input=None):
        """Step 1: ask adapter IP/port/unit and integration name."""
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=self._schema)

        self._data.update(user_input)
        errors = self._validate_inputs(self._data)
        if errors:
            return self.async_show_form(step_id="user", data_schema=self._schema, errors=errors)

        host = self._data.get(CONF_HOST)
        port = self._data.get(CONF_PORT)
        unit = self._data.get(CONF_UNIT)
        if host and port is not None and unit is not None:
            await self.async_set_unique_id(f"{host}:{port}:{unit}")
            self._abort_if_unique_id_configured()

        return await self.async_step_verify_adapter()

    async def async_step_verify_adapter(self, user_input=None):
        """Step 2: verify adapter reachability."""
        host = self._data.get(CONF_HOST)
        port = self._data.get(CONF_PORT)
        if not host or port is None:
            return await self.async_step_user()

        if self._verify_task is None:
            self._verify_task = asyncio.create_task(_async_test_connection(str(host), int(port)))

        if not self._verify_task.done():
            return self.async_show_progress(
                step_id="verify_adapter",
                progress_action="verify_adapter",
                progress_task=self._verify_task,
                description_placeholders={"host": str(host), "port": str(port)},
            )

        connection_error = await self._verify_task
        self._verify_task = None
        if connection_error is not None:
            return self.async_show_form(
                step_id="verify_adapter",
                data_schema=vol.Schema({}),
                errors={"base": connection_error},
                description_placeholders={"host": str(host), "port": str(port)},
            )

        return self.async_show_progress_done(next_step_id="probe_registers")

    async def async_step_probe_registers(self, user_input=None):
        """Step 3: probe all defined registers and save responding address list."""
        if self._probe_task is None:
            self._probe_task = asyncio.create_task(self._async_probe_and_fetch_identity())

        if not self._probe_task.done():
            return self.async_show_progress(
                step_id="probe_registers",
                progress_action="probe_registers",
                progress_task=self._probe_task,
            )

        responding, identity = await self._probe_task
        self._probe_task = None
        if not responding:
            return self.async_show_form(
                step_id="probe_registers",
                data_schema=vol.Schema({}),
                errors={"base": "probe_failed"},
            )

        self._data[CONF_RESPONDING_REGISTERS] = sorted(responding)

        if identity:
            self._data.update(identity)
            self._data[CONF_DEVICE_INFO_PENDING_FETCH] = False
            self._data[CONF_DEVICE_INFO_FETCH_ATTEMPTED] = True
        else:
            self._data[CONF_DEVICE_INFO_PENDING_FETCH] = True
            self._data[CONF_DEVICE_INFO_FETCH_ATTEMPTED] = False

        title = self._data.get(CONF_NAME, "Plum Ecovent")
        return self.async_create_entry(title=title, data=self._data)

    async def _async_probe_and_fetch_identity(self) -> tuple[list[int], dict[str, str]]:
        """Run long probe/identity operations in a tracked task for progress UI."""
        responding = await _async_probe_responding_registers(self.hass, self._data, retries=1)
        identity: dict[str, str] = {}
        if responding:
            identity = await _async_fetch_device_identity(self.hass, self._data)
        return responding, identity

    def _validate_inputs(self, data: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        port = data.get(CONF_PORT)
        if port is None or not (1 <= int(port) <= 65535):
            errors[CONF_PORT] = "invalid_port"
        unit = data.get(CONF_UNIT)
        if unit is None or not (1 <= int(unit) <= 247):
            errors[CONF_UNIT] = "invalid_unit"
        update_rate = data.get(CONF_UPDATE_RATE)
        if update_rate is None or not (1 <= int(update_rate) <= 3600):
            errors[CONF_UPDATE_RATE] = "invalid_update_rate"
        return errors

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for connection tuning, entity include/exclude, and device settings."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._device_settings_group: str | None = None

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input.get(CONF_OPTIONS_ACTION)
            if action == "connection":
                return await self.async_step_connection()
            if action == "entities":
                return await self.async_step_entities()
            if action == "device_settings":
                return await self.async_step_device_settings()

        return self.async_show_form(step_id="init", data_schema=self._menu_schema())

    async def async_step_connection(self, user_input=None):
        if user_input is not None:
            errors: dict[str, str] = {}

            host = user_input.get(CONF_HOST)
            port = user_input.get(CONF_PORT)
            rate = user_input.get(CONF_UPDATE_RATE)
            unit = user_input.get(CONF_UNIT)

            if rate is None or not (1 <= int(rate) <= 3600):
                errors[CONF_UPDATE_RATE] = "invalid_update_rate"
            if unit is None or not (1 <= int(unit) <= 247):
                errors[CONF_UNIT] = "invalid_unit"
            if port is None or not (1 <= int(port) <= 65535):
                errors[CONF_PORT] = "invalid_port"

            if not errors and host and port is not None:
                connection_error = await _async_test_connection(host, int(port))
                if connection_error is not None:
                    errors["base"] = connection_error

            if errors:
                return self.async_show_form(
                    step_id="connection",
                    data_schema=self._connection_schema(user_input),
                    errors=errors,
                )

            merged = self._current()
            merged.update(
                {
                    CONF_HOST: host,
                    CONF_PORT: int(port),
                    CONF_NAME: user_input.get(CONF_NAME, "Plum Ecovent"),
                    CONF_UPDATE_RATE: int(rate),
                    CONF_UNIT: int(unit),
                }
            )
            return self.async_create_entry(title="Options", data=merged)

        current = self._current()
        return self.async_show_form(step_id="connection", data_schema=self._connection_schema(current))

    async def async_step_entities(self, user_input=None):
        if user_input is not None:
            errors: dict[str, str] = {}

            forced = set(user_input.get(CONF_OPTIONAL_FORCE_ENABLE, []))
            disabled = set(user_input.get(CONF_OPTIONAL_DISABLE, []))
            if forced & disabled:
                errors["base"] = "overlapping_optional_overrides"

            if errors:
                return self.async_show_form(
                    step_id="entities",
                    data_schema=self._entities_schema(user_input),
                    errors=errors,
                )

            choices = self._entity_choices()
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

            merged = self._current()
            merged[CONF_OPTIONAL_FORCE_ENABLE] = sorted(set(forced) | set(unknown_forced))
            merged[CONF_OPTIONAL_DISABLE] = sorted(set(disabled) | set(unknown_disabled))
            return self.async_create_entry(title="Options", data=merged)

        current = self._current()
        return self.async_show_form(step_id="entities", data_schema=self._entities_schema(current))

    async def async_step_device_settings(self, user_input=None):
        if user_input is not None:
            group_id = user_input.get(CONF_DEVICE_SETTINGS_GROUP)
            if group_id:
                return await self.async_step_device_settings_group({CONF_DEVICE_SETTINGS_GROUP: group_id})

        return self.async_show_form(step_id="device_settings", data_schema=self._device_settings_menu_schema())

    async def async_step_device_settings_group(self, user_input=None):
        groups = self._device_setting_groups()

        if user_input is not None and CONF_DEVICE_SETTINGS_GROUP in user_input:
            group_id = user_input[CONF_DEVICE_SETTINGS_GROUP]
            self._device_settings_group = group_id
            return self.async_show_form(
                step_id="device_settings_group",
                data_schema=self._device_settings_group_schema(group_id),
                description_placeholders={"group_name": groups.get(group_id, {}).get("label", group_id)},
            )

        current_group = self._current_device_settings_group()
        if user_input is not None and current_group:
            errors: dict[str, str] = {}
            group_meta = groups.get(current_group, {})
            settings = group_meta.get("settings", [])

            values_to_write: dict[int, int] = {}
            persisted_values: dict[str, int] = dict(self._current().get(CONF_DEVICE_SETTINGS_VALUES, {}) or {})
            for setting in settings:
                key = setting["key"]
                value = user_input.get(key)
                min_value = setting.get("min")
                max_value = setting.get("max")
                if value is None:
                    continue
                if min_value is not None and value < min_value:
                    errors[key] = "invalid_device_setting"
                if max_value is not None and value > max_value:
                    errors[key] = "invalid_device_setting"
                values_to_write[int(setting["address"])] = int(value)
                persisted_values[key] = int(value)

            if not errors:
                config = self._current()
                write_ok = await _async_write_device_settings(self.hass, config, values_to_write)
                if not write_ok:
                    errors["base"] = "cannot_connect"

            if errors:
                return self.async_show_form(
                    step_id="device_settings_group",
                    data_schema=self._device_settings_group_schema(current_group, user_input),
                    errors=errors,
                    description_placeholders={"group_name": groups.get(current_group, {}).get("label", current_group)},
                )

            merged = self._current()
            merged[CONF_DEVICE_SETTINGS_VALUES] = persisted_values
            return self.async_create_entry(title="Options", data=merged)

        return self.async_show_form(step_id="device_settings", data_schema=self._device_settings_menu_schema())

    def _current(self) -> dict:
        return {**self._entry.data, **self._entry.options}

    def _menu_schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_OPTIONS_ACTION, default="connection"): vol.In(
                    {
                        "connection": "Modify connection and update settings",
                        "entities": "Select entities to include/exclude",
                        "device_settings": "Device Settings",
                    }
                )
            }
        )

    def _connection_schema(self, current: dict):
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=current.get(CONF_PORT, 502)): vol.All(vol.Coerce(int)),
                vol.Required(CONF_NAME, default=current.get(CONF_NAME, "Plum Ecovent")): str,
                vol.Required(CONF_UPDATE_RATE, default=current.get(CONF_UPDATE_RATE, DEFAULT_UPDATE_RATE)): vol.All(vol.Coerce(int)),
                vol.Required(CONF_UNIT, default=current.get(CONF_UNIT, 1)): vol.All(vol.Coerce(int)),
            }
        )

    def _entity_choices(self) -> dict[str, str]:
        from .registers import entity_catalog

        return entity_catalog()

    def _entities_schema(self, current: dict):
        choices = self._entity_choices()
        default_forced = [value for value in current.get(CONF_OPTIONAL_FORCE_ENABLE, []) if value in choices]
        default_disabled = [value for value in current.get(CONF_OPTIONAL_DISABLE, []) if value in choices]

        return vol.Schema(
            {
                vol.Optional(CONF_OPTIONAL_FORCE_ENABLE, default=default_forced): cv.multi_select(choices),
                vol.Optional(CONF_OPTIONAL_DISABLE, default=default_disabled): cv.multi_select(choices),
            }
        )

    def _device_settings_menu_schema(self):
        groups = self._device_setting_groups()
        return vol.Schema(
            {
                vol.Required(CONF_DEVICE_SETTINGS_GROUP): vol.In(
                    {group_id: group_meta["label"] for group_id, group_meta in groups.items()}
                )
            }
        )

    def _device_settings_group_schema(self, group_id: str, current_values: dict | None = None):
        groups = self._device_setting_groups()
        settings = groups.get(group_id, {}).get("settings", [])
        persisted = dict(self._current().get(CONF_DEVICE_SETTINGS_VALUES, {}) or {})
        current_values = current_values or {}
        schema_items: dict[Any, Any] = {}

        for setting in settings:
            key = setting["key"]
            fallback = persisted.get(key)
            if key in current_values:
                fallback = current_values[key]
            if fallback is None:
                fallback = setting.get("min") if setting.get("min") is not None else 0

            schema_items[vol.Required(key, default=fallback)] = vol.All(vol.Coerce(int))

        return vol.Schema(schema_items)

    def _current_device_settings_group(self) -> str | None:
        return self._device_settings_group

    def _device_setting_groups(self) -> dict[str, dict]:
        from .registers import device_setting_groups

        return device_setting_groups()


async def async_get_options_flow(entry: config_entries.ConfigEntry):
    return OptionsFlowHandler(entry)


async def _async_probe_responding_registers(hass, config: dict, retries: int = 2) -> list[int]:
    """Probe all defined register addresses and return those that respond."""
    manager = ModbusClientManager(hass, config)
    manager.retries = 0
    manager.backoff = 0.05
    manager.timeout = 1.5
    connected = await manager.async_connect()
    if not connected:
        return []

    try:
        addresses = _all_defined_addresses()
        responding: list[int] = []
        for address in addresses:
            success = False
            for _ in range(retries + 1):
                response = await manager.read_holding_registers(address, 1, return_error_response=True)
                if _is_illegal_data_response(response):
                    break
                if response is not None and hasattr(response, "registers"):
                    success = True
                    break
            if success:
                responding.append(address)
        return sorted(set(responding))
    finally:
        await manager.async_close()


def _all_defined_addresses() -> list[int]:
    from . import registers

    addresses: set[int] = set()
    for definition in [*registers.SENSORS, *registers.BINARY_SENSORS, *registers.SWITCHES, *registers.NUMBERS]:
        addresses.add(int(definition.address))
    return sorted(addresses)


def _is_illegal_data_response(response: Any) -> bool:
    """Return True when Modbus replied with illegal address/value style exception."""
    if response is None:
        return False
    is_error = getattr(response, "isError", None)
    try:
        if callable(is_error) and not is_error():
            return False
    except Exception:
        return False

    exception_code = getattr(response, "exception_code", None)
    if exception_code in (2, 3):
        return True

    message = str(response).lower()
    return "illegal" in message and ("address" in message or "data" in message or "value" in message)


async def _async_fetch_device_identity(hass, config: dict) -> dict[str, str]:
    """Read static device metadata registers once during config flow."""
    manager = ModbusClientManager(hass, config)
    connected = await manager.async_connect()
    if not connected:
        return {}

    try:
        result: dict[str, str] = {}

        firmware_response = await manager.read_holding_registers(16, 1)
        if firmware_response is not None and hasattr(firmware_response, "registers") and firmware_response.registers:
            firmware = format_firmware(firmware_response.registers[0])
            if firmware:
                result[CONF_FIRMWARE_VERSION] = firmware

        name_response = await manager.read_holding_registers(17, 8)
        if name_response is not None and hasattr(name_response, "registers") and name_response.registers:
            device_name = decode_utf8_registers(list(name_response.registers))
            if device_name:
                result[CONF_DEVICE_NAME] = device_name

        serial_response = await manager.read_holding_registers(25, 5)
        if serial_response is not None and hasattr(serial_response, "registers") and serial_response.registers:
            serial = decode_utf8_registers(list(serial_response.registers))
            if serial:
                result[CONF_DEVICE_SERIAL] = serial

        return result
    finally:
        await manager.async_close()


async def _async_write_device_settings(hass, config: dict, values_by_address: dict[int, int]) -> bool:
    """Write one or more configurable registers through a short-lived manager."""
    if not values_by_address:
        return True

    manager = ModbusClientManager(hass, config)
    connected = await manager.async_connect()
    if not connected:
        return False

    try:
        for address, value in values_by_address.items():
            success = await manager.write_register(int(address), int(value))
            if not success:
                return False
        return True
    finally:
        await manager.async_close()


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
