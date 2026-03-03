"""Tests for the config flow."""

import asyncio
import sys, os
# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from homeassistant import config_entries
import pytest

from custom_components.plum_ecovent.config_flow import ConfigFlow
from custom_components.plum_ecovent.const import (
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT,
    CONF_UPDATE_RATE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_OPTIONAL_DISABLE,
    CONF_RESPONDING_REGISTERS,
)
from homeassistant.const import CONF_NAME


async def _step_until_not_progress(step_coro_factory, max_attempts=10):
    result = await step_coro_factory()
    attempts = 0
    while result.get("type") == "progress" and attempts < max_attempts:
        await asyncio.sleep(0)
        result = await step_coro_factory()
        attempts += 1
    return result


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

    async def _probe(_hass, _config, retries=2):
        return [201, 202]

    monkeypatch.setattr(cf, "_async_test_connection", _ok_connection)
    monkeypatch.setattr(cf, "_async_fetch_device_identity", _identity)
    monkeypatch.setattr(cf, "_async_probe_responding_registers", _probe)
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
    assert result2["type"] == "progress"

    result3 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result3["type"] == "progress_done"

    result4 = await _step_until_not_progress(lambda: flow.async_step_probe_registers())
    assert result4["type"] == "progress_done"

    result5 = await flow.async_step_probe_registers_result()
    assert result5["type"] == "create_entry"
    assert result5["title"] == "My"
    assert result5["data"][CONF_HOST] == "1.2.3.4"
    assert result5["data"][CONF_PORT] == 502
    assert result5["data"][CONF_UNIT] == 17
    assert result5["data"][CONF_RESPONDING_REGISTERS] == [201, 202]

    # invalid port should return form with error
    result6 = await flow.async_step_user(
        {CONF_HOST: "1.2.3.4", CONF_PORT: 70000, CONF_UNIT: 1, CONF_UPDATE_RATE: 30}
    )
    assert result6["type"] == "form"
    assert result6["errors"][CONF_PORT] == "invalid_port"

    # invalid unit should return form with error
    result7 = await flow.async_step_user(
        {CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 0, CONF_UPDATE_RATE: 30}
    )
    assert result7["type"] == "form"
    assert result7["errors"][CONF_UNIT] == "invalid_unit"


@pytest.mark.asyncio
async def test_tcp_flow_verify_adapter_connection_error(monkeypatch):
    """Flow should surface adapter verification errors at verify step."""
    flow = ConfigFlow()
    import custom_components.plum_ecovent.config_flow as cf

    async def _refused_connection(host, port, timeout=5.0):
        return "connection_refused"

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_test_connection", _refused_connection)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    result = await flow.async_step_user(
        {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 502,
            CONF_UNIT: 1,
            CONF_UPDATE_RATE: 30,
            CONF_NAME: "My",
        }
    )
    assert result["type"] == "progress"

    result2 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result2["type"] == "progress_done"

    result3 = await flow.async_step_verify_adapter_result()
    assert result3["type"] == "form"
    assert result3["step_id"] == "verify_adapter"
    assert result3["errors"]["base"] == "connection_refused"


@pytest.mark.asyncio
@pytest.mark.parametrize("error_code", ["connection_timeout", "invalid_host"])
async def test_tcp_flow_verify_adapter_other_connection_errors(monkeypatch, error_code):
    """Flow should expose timeout and invalid host errors at verify step."""
    flow = ConfigFlow()
    import custom_components.plum_ecovent.config_flow as cf

    async def _failing_connection(host, port, timeout=5.0):
        return error_code

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_test_connection", _failing_connection)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    result = await flow.async_step_user(
        {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 502,
            CONF_UNIT: 1,
            CONF_UPDATE_RATE: 30,
            CONF_NAME: "My",
        }
    )
    assert result["type"] == "progress"

    result2 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result2["type"] == "progress_done"

    result3 = await flow.async_step_verify_adapter_result()
    assert result3["type"] == "form"
    assert result3["step_id"] == "verify_adapter"
    assert result3["errors"]["base"] == error_code


@pytest.mark.asyncio
async def test_tcp_flow_probe_failed(monkeypatch):
    """Flow should show probe_failed when no registers respond."""
    flow = ConfigFlow()
    import custom_components.plum_ecovent.config_flow as cf

    async def _ok_connection(host, port, timeout=5.0):
        return None

    async def _probe_none(_hass, _config, retries=2):
        return []

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_test_connection", _ok_connection)
    monkeypatch.setattr(cf, "_async_probe_responding_registers", _probe_none)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    result = await flow.async_step_user(
        {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 502,
            CONF_UNIT: 1,
            CONF_UPDATE_RATE: 30,
            CONF_NAME: "My",
        }
    )
    assert result["type"] == "progress"

    result2 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result2["type"] == "progress_done"

    result3 = await _step_until_not_progress(lambda: flow.async_step_probe_registers())
    assert result3["type"] == "progress_done"

    result4 = await flow.async_step_probe_registers_result()
    assert result4["type"] == "form"
    assert result4["step_id"] == "probe_registers"
    assert result4["errors"]["base"] == "probe_failed"


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


@pytest.mark.asyncio
async def test_options_flow_branching_connection(monkeypatch):
    """Options flow should route to connection step and validate values."""
    from custom_components.plum_ecovent.config_flow import OptionsFlowHandler
    from types import SimpleNamespace
    import custom_components.plum_ecovent.config_flow as cf

    async def _ok_connection(host, port, timeout=5.0):
        return None

    monkeypatch.setattr(cf, "_async_test_connection", _ok_connection)

    entry = SimpleNamespace(
        data={
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 502,
            CONF_UNIT: 1,
            CONF_UPDATE_RATE: 30,
            CONF_NAME: "Plum",
        },
        options={},
    )
    flow = OptionsFlowHandler(entry)

    init_result = await flow.async_step_init()
    assert init_result["type"] == "form"
    assert init_result["step_id"] == "init"

    route_result = await flow.async_step_init({"options_action": "connection"})
    assert route_result["type"] == "form"
    assert route_result["step_id"] == "connection"

    invalid = await flow.async_step_connection(
        {
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 70000,
            CONF_UNIT: 1,
            CONF_UPDATE_RATE: 30,
            CONF_NAME: "Plum",
        }
    )
    assert invalid["type"] == "form"
    assert invalid["errors"][CONF_PORT] == "invalid_port"

    valid = await flow.async_step_connection(
        {
            CONF_HOST: "10.0.0.2",
            CONF_PORT: 502,
            CONF_UNIT: 7,
            CONF_UPDATE_RATE: 20,
            CONF_NAME: "New Name",
        }
    )
    assert valid["type"] == "create_entry"
    assert valid["data"][CONF_HOST] == "10.0.0.2"
    assert valid["data"][CONF_UNIT] == 7
    assert valid["data"][CONF_NAME] == "New Name"


@pytest.mark.asyncio
async def test_options_flow_branching_entities(monkeypatch):
    """Options flow should route to entities step and reject overlap."""
    from custom_components.plum_ecovent.config_flow import OptionsFlowHandler
    from types import SimpleNamespace
    import custom_components.plum_ecovent.config_flow as cf

    monkeypatch.setattr(cf.OptionsFlowHandler, "_entity_choices", lambda self: {"sensor:82:co2": "sensor · CO2 (82)"})

    entry = SimpleNamespace(
        data={
            CONF_HOST: "1.2.3.4",
            CONF_PORT: 502,
            CONF_UNIT: 1,
            CONF_UPDATE_RATE: 30,
            CONF_NAME: "Plum",
        },
        options={},
    )
    flow = OptionsFlowHandler(entry)

    route_result = await flow.async_step_init({"options_action": "entities"})
    assert route_result["type"] == "form"
    assert route_result["step_id"] == "entities"

    overlap = await flow.async_step_entities(
        {
            CONF_OPTIONAL_FORCE_ENABLE: ["sensor:82:co2"],
            CONF_OPTIONAL_DISABLE: ["sensor:82:co2"],
        }
    )
    assert overlap["type"] == "form"
    assert overlap["errors"]["base"] == "overlapping_optional_overrides"

    valid = await flow.async_step_entities(
        {
            CONF_OPTIONAL_FORCE_ENABLE: ["sensor:82:co2"],
            CONF_OPTIONAL_DISABLE: [],
        }
    )
    assert valid["type"] == "create_entry"
    assert valid["data"][CONF_OPTIONAL_FORCE_ENABLE] == ["sensor:82:co2"]
