import asyncio
import sys, os
# make custom_components importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from custom_components.plum_ecovent.modbus_client import ModbusClientManager
from custom_components.plum_ecovent.const import CONF_HOST, CONF_PORT, CONF_UNIT


class DummyClient:
    async def read_holding_registers(self, *args, **kwargs):
        raise Exception("read failure")

    async def write_register(self, *args, **kwargs):
        raise Exception("write failure")

    async def close(self):
        raise Exception("close failure")


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
