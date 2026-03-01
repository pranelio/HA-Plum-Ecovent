"""Async Modbus client manager for Plum Ecovent.

Provides a small wrapper around pymodbus async clients supporting TCP and RTU.
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
    CONF_MODBUS_TYPE,
    MODBUS_TYPE_TCP,
    CONF_HOST,
    CONF_PORT,
    CONF_SERIAL_PORT,
    CONF_BAUDRATE,
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
            # Import async client classes with fallback for pymodbus versions
            # Avoid direct `import ... async` which is invalid syntax by using importlib
            import importlib

            try:
                mod = importlib.import_module("pymodbus.client.async_io")
            except Exception:
                mod = importlib.import_module("pymodbus.client.async")

            AsyncModbusTcpClient = getattr(mod, "AsyncModbusTcpClient")
            AsyncModbusSerialClient = getattr(mod, "AsyncModbusSerialClient")

            if self.config.get(CONF_MODBUS_TYPE) == MODBUS_TYPE_TCP:
                host = self.config.get(CONF_HOST)
                port = int(self.config.get(CONF_PORT, 502))
                self._client = AsyncModbusTcpClient(host=host, port=port)
            else:
                port = self.config.get(CONF_SERIAL_PORT)
                baudrate = int(self.config.get(CONF_BAUDRATE, 9600))
                self._client = AsyncModbusSerialClient(
                    method="rtu", port=port, baudrate=baudrate
                )

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
            result = await self._client.read_holding_registers(
                address, count, unit=use_unit
            )
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
            result = await self._client.write_register(address, value, unit=use_unit)
            return result is not None
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error writing register")
            return False
