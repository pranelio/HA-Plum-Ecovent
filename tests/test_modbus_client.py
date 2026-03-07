import asyncio
import sys, os
# make custom_components importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from custom_components.plum_ecovent.modbus_client import ModbusClientManager
from custom_components.plum_ecovent.const import (
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT,
    CONNECTION_TYPE_RTU,
)


class DummyClient:
    async def read_holding_registers(self, *args, **kwargs):
        raise Exception("read failure")

    async def write_register(self, *args, **kwargs):
        raise Exception("write failure")

    async def close(self):
        raise Exception("close failure")


class PositionalClient:
    """Client where read/write expect unit as positional arg."""
    def __init__(self):
        self.record = []

    async def read_holding_registers(self, address, count, unit):
        self.record.append((address, count, unit))
        class R:
            registers = [1]
        return R()

    async def write_register(self, address, value, unit):
        self.record.append((address, value, unit))
        return True

    async def close(self):
        pass


class NoUnitClient:
    """Client whose methods take only address and count/value."""
    def __init__(self):
        self.record = []

    async def read_holding_registers(self, address, count):
        self.record.append((address, count))
        class R:
            registers = [2]
        return R()

    async def write_register(self, address, value):
        self.record.append((address, value))
        return True

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_manager_read_write_exceptions():
    """Verify read/write return safe values when the client is missing or bad."""
    mgr = ModbusClientManager(None, {CONF_UNIT: 3})
    # no client
    assert await mgr.read_holding_registers(1, 1) is None
    assert not await mgr.write_register(1, 2)

    # attach a dummy client that always throws
    mgr._client = DummyClient()
    assert await mgr.read_holding_registers(1, 1) is None
    assert not await mgr.write_register(1, 2)

    # closing should swallow the exception
    await mgr.async_close()


@pytest.mark.asyncio
async def test_async_connect_import_failure(monkeypatch):
    """If pymodbus can't be imported the connect method returns False."""
    mgr = ModbusClientManager(None, {CONF_HOST: "1.2.3.4", CONF_PORT: 502})

    # monkeypatch import_module to simulate ImportError
    import importlib

    def fake_import(name):
        raise Exception("no module")

    monkeypatch.setattr(importlib, "import_module", fake_import)
    result = await mgr.async_connect()
    assert result is False


@pytest.mark.asyncio
async def test_async_connect_no_async_class(monkeypatch, caplog):
    """Logging occurs when module is present but class is missing."""
    mgr = ModbusClientManager(None, {CONF_HOST: "1.2.3.4", CONF_PORT: 502})

    class DummyMod:
        pass

    import importlib
    # return DummyMod for any requested module name
    monkeypatch.setattr(importlib, "import_module", lambda name: DummyMod)

    caplog.set_level("ERROR")
    result = await mgr.async_connect()
    assert result is False
    assert "pymodbus asynchronous client class not found" in caplog.text


@pytest.mark.asyncio
async def test_async_connect_success(monkeypatch):
    """Simulate a working AsyncModbusTcpClient with connect/close methods."""
    mgr = ModbusClientManager(None, {CONF_HOST: "1.2.3.4", CONF_PORT: 502})

    class FakeClient:
        def __init__(self, host=None, port=None):
            self.host = host
            self.port = port

        async def connect(self):
            return True

        async def close(self):
            return True

    # fake module returned by import_module
    class FakeMod:
        AsyncModbusTcpClient = FakeClient
        AsyncModbusSerialClient = FakeClient

    import importlib

    monkeypatch.setattr(importlib, "import_module", lambda name: FakeMod)
    ok = await mgr.async_connect()
    assert ok is True
    # ensure client stored with correct args
    assert isinstance(mgr._client, FakeClient)
    assert mgr._client.host == "1.2.3.4"
    assert mgr._client.port == 502
    # close should not error
    await mgr.async_close()


@pytest.mark.asyncio
async def test_read_write_positional_unit():
    """When client expects the unit argument positionally, our fallback works."""
    mgr = ModbusClientManager(None, {CONF_UNIT: 9})
    mgr._client = PositionalClient()
    res = await mgr.read_holding_registers(5, 1)
    assert hasattr(res, "registers") and res.registers[0] == 1
    assert mgr._client.record[0] == (5, 1, 9)
    ok = await mgr.write_register(5, 12)
    assert ok is True
    assert mgr._client.record[1] == (5, 12, 9)


@pytest.mark.asyncio
async def test_read_write_no_unit():
    """Clients that ignore unit altogether should still work."""
    mgr = ModbusClientManager(None, {CONF_UNIT: 11})
    mgr._client = NoUnitClient()
    res = await mgr.read_holding_registers(7, 2)
    assert hasattr(res, "registers") and res.registers[0] == 2
    assert mgr._client.record[0] == (7, 2)
    ok = await mgr.write_register(7, 33)
    assert ok is True
    assert mgr._client.record[1] == (7, 33)


@pytest.mark.asyncio
async def test_async_connect_rtu_not_implemented(caplog):
    """RTU transport path is intentionally blocked until implemented."""
    mgr = ModbusClientManager(None, {CONF_CONNECTION_TYPE: CONNECTION_TYPE_RTU})
    caplog.set_level("ERROR")

    result = await mgr.async_connect()

    assert result is False
    assert "Modbus RTU transport is not implemented yet" in caplog.text
