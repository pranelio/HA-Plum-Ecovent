"""Async Modbus client manager for Plum Ecovent.

Provides a small wrapper around a pymodbus async TCP client.
"""
from __future__ import annotations

import logging
import inspect
import asyncio
import time
from typing import Any

try:
    from pymodbus.exceptions import ModbusException
    from pymodbus.exceptions import ConnectionException
except Exception:  # pymodbus not installed in test environments
    class ModbusException(Exception):
        pass

    class ConnectionException(ModbusException):
        pass

from .const import (
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONNECTION_TYPE_RTU,
    CONNECTION_TYPE_TCP,
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
        self.transport = str(self.config.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_TCP) or CONNECTION_TYPE_TCP).lower()
        # unit id (slave address)
        from .const import DEFAULT_UNIT, CONF_UNIT
        self.unit = int(self.config.get(CONF_UNIT, DEFAULT_UNIT))
        self.retries = 2
        self.backoff = 0.2
        self.timeout = 5.0
        self.reconnect_interval = 10.0
        self._last_reconnect_attempt = 0.0
        self._retry_counter = 0
        self._closing = False
        self._connection_was_lost = False
        self._io_lock = asyncio.Lock()
        self.request_spacing = 0.03
        self._last_io_time = 0.0

    @property
    def retry_counter(self) -> int:
        """Total number of retry attempts performed after an initial failure."""
        return self._retry_counter

    def _increment_retry_counter(self) -> None:
        self._retry_counter += 1

    async def _async_mark_connection_lost(self) -> None:
        """Mark current client connection as lost and close it."""
        if self._client is None:
            return
        self._connection_was_lost = True
        await self.async_close()
        self._client = None

    async def async_ensure_connected(self, *, force: bool = False) -> bool:
        """Ensure a live client connection exists.

        Reconnect attempts are rate-limited to avoid tight loops when the
        device is offline.
        """
        if self._client is not None:
            return True

        if self._closing:
            return False

        now = time.monotonic()
        elapsed = now - self._last_reconnect_attempt
        if not force and elapsed < self.reconnect_interval:
            return False

        self._last_reconnect_attempt = now
        self._increment_retry_counter()
        if self._connection_was_lost:
            _LOGGER.warning("Attempting Modbus reconnect after communication loss")
        return await self.async_connect()

    async def async_connect(self) -> bool:
        """Create and connect the underlying pymodbus async client."""
        if self._closing:
            return False
        if self.transport == CONNECTION_TYPE_RTU:
            _LOGGER.error("Modbus RTU transport is not implemented yet")
            return False
        if self.transport != CONNECTION_TYPE_TCP:
            _LOGGER.error("Unsupported Modbus transport '%s'", self.transport)
            return False
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
                    "Ensure pymodbus>=3.10.0 is installed in the Home Assistant "
                    "environment",
                    tried,
                )
                return False

            host = self.config.get(CONF_HOST)
            port = int(self.config.get(CONF_PORT, 502))
            self._client = self._build_client(
                host=host,
                port=port,
                async_modbus_tcp_client=AsyncModbusTcpClient,
                async_modbus_serial_client=AsyncModbusSerialClient,
            )
            if self._client is None:
                return False

            connect = getattr(self._client, "connect", None)
            if connect is not None:
                result = await connect()
                _LOGGER.debug("Modbus connect result: %s", result)
                if result is False:
                    _LOGGER.error("Modbus connect() returned falsy result")
                    return False

            self._connection_was_lost = False
            return True
        except ModbusException as err:
            _LOGGER.exception("Failed to start Modbus client: %s", err)
            return False
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating Modbus client")
            return False

    def _build_client(
        self,
        *,
        host: Any,
        port: int,
        async_modbus_tcp_client: Any,
        async_modbus_serial_client: Any,
    ) -> Any | None:
        """Build transport-specific pymodbus client (TCP now, RTU later)."""
        if self.transport == CONNECTION_TYPE_TCP:
            return async_modbus_tcp_client(host=host, port=port)

        if self.transport == CONNECTION_TYPE_RTU:
            _LOGGER.error("Modbus RTU transport is not implemented yet")
            return None

        _LOGGER.error("Unsupported Modbus transport '%s'", self.transport)
        return None

    async def async_close(self) -> None:
        """Close the underlying client connection."""
        self._closing = True
        if not self._client:
            return
        close = getattr(self._client, "close", None)
        if close is not None:
            try:
                result = close()
                if inspect.isawaitable(result):
                    result = await result
                _LOGGER.debug("Modbus close result: %s", result)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error closing Modbus client")
            finally:
                self._client = None

    async def read_holding_registers(
        self,
        address: int,
        count: int,
        unit: int | None = None,
        return_error_response: bool = False,
    ) -> Any:
        """Read holding registers — returns pymodbus result or None."""
        async with self._io_lock:
            if not await self.async_ensure_connected():
                _LOGGER.debug("No Modbus client available for read")
                return None
            try:
                use_unit = self.unit if unit is None else unit
                # some pymodbus versions expect `unit` keyword, others take it as
                # positional argument or ignore it entirely.  try a sequence of
                # combinations until one works.
                result = None
                for attempt in range(self.retries + 1):
                    if attempt > 0:
                        self._increment_retry_counter()
                        await self._async_mark_connection_lost()
                        if not await self.async_ensure_connected(force=True):
                            if attempt < self.retries:
                                await asyncio.sleep(self.backoff * (attempt + 1))
                            continue
                    for call in (
                        lambda: self._client.read_holding_registers(address, count),
                        lambda: self._client.read_holding_registers(address=address, count=count),
                        lambda: self._client.read_holding_registers(address, count, use_unit),
                        lambda: self._client.read_holding_registers(address=address, count=count, unit=use_unit),
                        lambda: self._client.read_holding_registers(address=address, count=count, slave=use_unit),
                        lambda: self._client.read_holding_registers(address),
                    ):
                        try:
                            await self._async_wait_request_spacing()
                            result = call()
                            if inspect.isawaitable(result):
                                try:
                                    result = await asyncio.wait_for(result, timeout=self.timeout)
                                except asyncio.CancelledError:
                                    _LOGGER.debug("Modbus read cancelled (likely due to unload)")
                                    return None
                            break
                        except TypeError:
                            result = None
                            continue
                        except (ConnectionException, asyncio.TimeoutError):
                            result = None
                            await self._async_mark_connection_lost()
                            break
                        except ModbusException as err:
                            message = str(err).lower()
                            if "request cancelled outside pymodbus" in message or self._closing:
                                _LOGGER.debug("Modbus read cancelled while unloading")
                                return None
                            result = None
                            await self._async_mark_connection_lost()
                            break

                    if result is not None and not self._response_matches_expected(result, use_unit, expected_function=3):
                        _LOGGER.warning(
                            "Discarding Modbus response with unexpected unit/function for address %s; retrying",
                            address,
                        )
                        result = None
                        await self._async_mark_connection_lost()

                    if result is not None:
                        break
                    if attempt < self.retries:
                        await asyncio.sleep(self.backoff * (attempt + 1))
                    else:
                        _LOGGER.warning("Modbus read failed after retries for address %s", address)
                        return None

                # some pymodbus results expose isError()
                if result is not None and hasattr(result, "isError") and callable(result.isError):
                    if result.isError():
                        if return_error_response:
                            return result
                        _LOGGER.error("Modbus read returned error response for address %s", address)
                        return None
                return result
            except ConnectionException:
                _LOGGER.warning("Modbus connection error during read")
                await self._async_mark_connection_lost()
                return None
            except asyncio.CancelledError:
                _LOGGER.debug("Modbus read cancelled")
                return None
            except ModbusException as err:
                message = str(err).lower()
                if "request cancelled outside pymodbus" in message or self._closing:
                    _LOGGER.debug("Modbus read cancelled while unloading")
                    return None
                _LOGGER.warning("Modbus error during read: %s", err)
                await self._async_mark_connection_lost()
                return None
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error reading holding registers")
                return None

    async def write_register(
        self, address: int, value: int, unit: int | None = None
    ) -> bool:
        """Write single register. Returns True on success."""
        async with self._io_lock:
            if not await self.async_ensure_connected():
                _LOGGER.debug("No Modbus client available for write")
                return False
            try:
                use_unit = self.unit if unit is None else unit
                result = None
                for attempt in range(self.retries + 1):
                    if attempt > 0:
                        self._increment_retry_counter()
                        await self._async_mark_connection_lost()
                        if not await self.async_ensure_connected(force=True):
                            if attempt < self.retries:
                                await asyncio.sleep(self.backoff * (attempt + 1))
                            continue
                    for call in (
                        lambda: self._client.write_register(address, value),
                        lambda: self._client.write_register(address=address, value=value),
                        lambda: self._client.write_register(address, value, use_unit),
                        lambda: self._client.write_register(address=address, value=value, unit=use_unit),
                        lambda: self._client.write_register(address=address, value=value, slave=use_unit),
                    ):
                        try:
                            await self._async_wait_request_spacing()
                            result = call()
                            if inspect.isawaitable(result):
                                try:
                                    result = await asyncio.wait_for(result, timeout=self.timeout)
                                except asyncio.CancelledError:
                                    _LOGGER.debug("Modbus write cancelled (likely due to unload)")
                                    return False
                            break
                        except TypeError:
                            result = None
                            continue
                        except (ConnectionException, asyncio.TimeoutError):
                            result = None
                            await self._async_mark_connection_lost()
                            break
                        except ModbusException as err:
                            message = str(err).lower()
                            if "request cancelled outside pymodbus" in message or self._closing:
                                _LOGGER.debug("Modbus write cancelled while unloading")
                                return False
                            result = None
                            await self._async_mark_connection_lost()
                            break

                    if result is not None and not self._response_matches_expected(result, use_unit, expected_function=6):
                        _LOGGER.warning(
                            "Discarding Modbus write response with unexpected unit/function for address %s; retrying",
                            address,
                        )
                        result = None
                        await self._async_mark_connection_lost()

                    if result is not None:
                        break
                    if attempt < self.retries:
                        await asyncio.sleep(self.backoff * (attempt + 1))
                    else:
                        _LOGGER.warning("Modbus write failed after retries for address %s", address)
                        return False

                if result is not None and hasattr(result, "isError") and callable(result.isError):
                    if result.isError():
                        _LOGGER.error("Modbus write returned error response for address %s", address)
                        return False

                return result is not None
            except ConnectionException:
                _LOGGER.warning("Modbus connection error during write")
                await self._async_mark_connection_lost()
                return False
            except asyncio.CancelledError:
                _LOGGER.debug("Modbus write cancelled")
                return False
            except ModbusException as err:
                message = str(err).lower()
                if "request cancelled outside pymodbus" in message or self._closing:
                    _LOGGER.debug("Modbus write cancelled while unloading")
                    return False
                _LOGGER.warning("Modbus error during write: %s", err)
                await self._async_mark_connection_lost()
                return False
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Error writing register")
                return False

    async def _async_wait_request_spacing(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_io_time
        if elapsed < self.request_spacing:
            await asyncio.sleep(self.request_spacing - elapsed)
        self._last_io_time = time.monotonic()

    def _response_matches_expected(self, response: Any, expected_unit: int, expected_function: int) -> bool:
        try:
            response_unit = None
            for attr_name in ("unit_id", "slave_id", "slave", "dev_id"):
                attr_value = getattr(response, attr_name, None)
                if attr_value is not None:
                    response_unit = int(attr_value)
                    break

            if response_unit is not None and int(response_unit) != int(expected_unit):
                return False

            function_code = getattr(response, "function_code", None)
            if function_code is not None:
                function_code = int(function_code)
                if function_code not in (expected_function, expected_function + 0x80):
                    return False
        except Exception:
            return True
        return True
