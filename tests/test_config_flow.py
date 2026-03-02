"""Tests for the config flow."""

import sys, os
# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from homeassistant import config_entries
import pytest

from custom_components.plum_ecovent.config_flow import ConfigFlow
from custom_components.plum_ecovent.const import CONF_HOST, CONF_PORT, CONF_UNIT, CONF_UPDATE_RATE
from homeassistant.const import CONF_NAME


@pytest.mark.asyncio
async def test_tcp_flow(monkeypatch):
    """Test that the flow creates an entry with TCP settings.

    We don't have the Home Assistant fixture available, so stub out the
    methods that would normally interact with hass.
    """
    flow = ConfigFlow()
    import custom_components.plum_ecovent.config_flow as cf

    async def _ok_connection(host, port, timeout=5.0):
        return None

    async def _identity(_hass, _config):
        return {}

    monkeypatch.setattr(cf, "_async_test_connection", _ok_connection)
    monkeypatch.setattr(cf, "_async_fetch_device_identity", _identity)
    # patch out hass-dependent helpers since we don't run under HA
    async def _dummy_set_unique_id(*args, **kwargs):
        return None
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    result = await flow.async_step_user()
    assert result["type"] == "form"

    user_input = {
        CONF_HOST: "1.2.3.4",
        CONF_PORT: 502,
        CONF_UNIT: 17,
        CONF_UPDATE_RATE: 30,
        CONF_NAME: "My",
    }
    result2 = await flow.async_step_user(user_input)
    assert result2["type"] == "create_entry"
    assert result2["title"] == "My"
    assert result2["data"][CONF_HOST] == "1.2.3.4"
    assert result2["data"][CONF_PORT] == 502
    assert result2["data"][CONF_UNIT] == 17

    # invalid port should return form with error
    result3 = await flow.async_step_user(
        {CONF_HOST: "1.2.3.4", CONF_PORT: 70000, CONF_UNIT: 1, CONF_UPDATE_RATE: 30}
    )
    assert result3["type"] == "form"
    assert result3["errors"][CONF_PORT] == "invalid_port"

    # invalid unit should return form with error
    result4 = await flow.async_step_user(
        {CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 0, CONF_UPDATE_RATE: 30}
    )
    assert result4["type"] == "form"
    assert result4["errors"][CONF_UNIT] == "invalid_unit"


# additional helper test for setup_entry device registration

class DummyRegistry:
    def __init__(self):
        self.created = []
    def async_get_or_create(self, **kwargs):
        self.created.append(kwargs)
        return kwargs


@pytest.mark.asyncio
async def test_async_setup_entry_creates_device(monkeypatch):
    """The entry setup should register a device in the device registry."""
    from custom_components.plum_ecovent import async_setup_entry
    from homeassistant.helpers import device_registry as dr
    from types import SimpleNamespace
    from custom_components.plum_ecovent.const import DOMAIN

    async def fake_forward(entry, p):
        return []

    hass = SimpleNamespace(
        data={},
        config_entries=SimpleNamespace(
            async_forward_entry_setups=fake_forward,
            async_update_entry=lambda *args, **kwargs: None,
        ),
    )
    registry = DummyRegistry()
    def fake_get(hass_obj):
        return registry
    monkeypatch.setattr(dr, "async_get", fake_get)

    # also make ModbusClientManager.async_connect always succeed so setup_entry
    # continues past the connection check
    from custom_components.plum_ecovent.modbus_client import ModbusClientManager
    async def always_connect(self):
        return True
    monkeypatch.setattr(ModbusClientManager, "async_connect", always_connect)

    import custom_components.plum_ecovent as integration

    async def fake_discover(manager, registers_module, config):
        return {"sensor": [], "binary_sensor": [], "switch": [], "number": []}

    class DummyCoordinator:
        def __init__(self, hass, manager, defs, update_rate):
            self.hass = hass
            self.manager = manager
            self.data = {}
            self.last_update_success = True

        async def async_config_entry_first_refresh(self):
            return None

    monkeypatch.setattr(integration, "_async_discover_definitions", fake_discover)
    monkeypatch.setattr(integration, "PlumEcoventCoordinator", DummyCoordinator)

    entry = SimpleNamespace(
        entry_id="abc123",
        title="MyUnit",
        data={},
        options={},
        async_on_unload=lambda *args, **kwargs: None,
        add_update_listener=lambda listener: listener,
    )
    result = await async_setup_entry(hass, entry)
    assert result is True
    # ensure our dummy registry was used and received identifiers
    assert registry.created, "device registry not invoked"
    assert registry.created[0]["identifiers"] == {(DOMAIN, entry.entry_id)}
