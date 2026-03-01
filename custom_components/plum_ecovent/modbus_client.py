"""Async Modbus client manager for Plum Ecovent.

Provides a small wrapper around a pymodbus async TCP client.
"""
from __future__ import annotations

import logging
from typing import Any

try:
    from pymodbus.exceptions import ModbusException
except Exception:  # pymodbus not installed in test environments
    class ModbusException(Exception):
        pass

from .const import (
    CONF_HOST,
    CONF_PORT,
)

_LOGGER = logging.getLogger(__name__)


class ModbusClientManager:
    """Manage an async pymodbus client instance.

    This is a lightweight wrapper used by the integration to open/close
    a client and provide simple read/write helpers. It intentionally keeps
    logic minimal — expand as needed for retries/timeouts.
    """

    def __init__(self, hass, config: dict) -> None:
        self.hass = hass
        self.config = config
        self._client = None
        # unit id (slave address)
        from .const import DEFAULT_UNIT, CONF_UNIT
        self.unit = int(self.config.get(CONF_UNIT, DEFAULT_UNIT))

    async def async_connect(self) -> bool:
        """Create and connect the underlying pymodbus async client."""
        try:
                # dynamic import of the async client class - pymodbus has moved
            # names across releases.  We try the known locations in order and
            # log a clear error if none of them are available.
            import importlib

            AsyncModbusTcpClient = None
            AsyncModbusSerialClient = None
            tried = []
            # perform imports in executor when possible, otherwise fall back
            for modname in (
                "pymodbus.client.async_io",
                "pymodbus.client.async",
                "pymodbus.client",
            ):
                try:
                    if self.hass is not None and hasattr(self.hass, "async_add_executor_job"):
                        mod = await self.hass.async_add_executor_job(importlib.import_module, modname)
                    else:
                        # running in test context or no hass available
                        mod = importlib.import_module(modname)
                    AsyncModbusTcpClient = getattr(mod, "AsyncModbusTcpClient", None)
                    AsyncModbusSerialClient = getattr(mod, "AsyncModbusSerialClient", None)
                    if AsyncModbusTcpClient:
                        break
                except ModuleNotFoundError:
                    tried.append(modname)
                    continue
                except Exception:
                    tried.append(modname)
                    continue
            if AsyncModbusTcpClient is None:
                _LOGGER.error(
                    "pymodbus asynchronous client class not found; tried %s. "
                    "Ensure pymodbus>=2.5 is installed in the Home Assistant "
                    "environment",
                    tried,
                )
                return False

            # always use TCP; serial/RTU removed
            host = self.config.get(CONF_HOST)
            port = int(self.config.get(CONF_PORT, 502))
            self._client = AsyncModbusTcpClient(host=host, port=port)

            connect = getattr(self._client, "connect", None)
            if connect is not None:
                result = await connect()
                _LOGGER.debug("Modbus connect result: %s", result)

            return True
        except ModbusException as err:
            _LOGGER.exception("Failed to start Modbus client: %s", err)
            return False
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating Modbus client")
            return False

    async def async_close(self) -> None:
        """Close the underlying client connection."""
        if not self._client:
            return
        close = getattr(self._client, "close", None)
        if close is not None:
            try:
                result = await close()
                _LOGGER.debug("Modbus close result: %s", result)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error closing Modbus client")

    async def read_holding_registers(
        self, address: int, count: int, unit: int | None = None
    ) -> Any:
        """Read holding registers — returns pymodbus result or None."""
        if not self._client:
            _LOGGER.debug("No Modbus client available for read")
            return None
        try:
            use_unit = self.unit if unit is None else unit
            # some pymodbus versions expect `unit` keyword, others take it as
            # positional argument or ignore it entirely.  try a sequence of
            # combinations until one works.
            try:
                result = await self._client.read_holding_registers(
                    address, count, unit=use_unit
                )
            except TypeError:
                try:
                    result = await self._client.read_holding_registers(
                        address, count, use_unit
                    )
                except TypeError:
                    # maybe the method doesn't accept a unit at all
                    result = await self._client.read_holding_registers(address, count)
            return result
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error reading holding registers")
            return None

    async def write_register(
        self, address: int, value: int, unit: int | None = None
    ) -> bool:
        """Write single register. Returns True on success."""
        if not self._client:
            _LOGGER.debug("No Modbus client available for write")
            return False
        try:
            use_unit = self.unit if unit is None else unit
            try:
                result = await self._client.write_register(address, value, unit=use_unit)
            except TypeError:
                try:
                    result = await self._client.write_register(address, value, use_unit)
                except TypeError:
                    result = await self._client.write_register(address, value)
            return result is not None
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error writing register")
            return False
