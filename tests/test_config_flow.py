"""Tests for the config flow."""

import asyncio
import sys, os
# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from homeassistant import config_entries
import pytest

from custom_components.plum_ecovent.config_flow import ConfigFlow
from custom_components.plum_ecovent.const import (
    CONF_AVAILABLE_REGISTERS,
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_NON_RESPONDING_REGISTERS,
    CONF_PORT,
    CONF_UNSUPPORTED_REGISTERS,
    CONF_UNIT,
    CONF_UPDATE_RATE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_OPTIONAL_DISABLE,
    CONF_RESPONDING_REGISTERS,
    CONNECTION_TYPE_RTU,
    CONNECTION_TYPE_TCP,
)


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

    async def _ok_connection(_hass, _config, retries=2, backoff=0.2):
        return None

    async def _identity(_hass, _config):
        return {}

    async def _probe(_hass, _config, max_attempts=3, deadline_seconds=45.0):
        return {
            "available": [201, 202],
            "non_responding": [203],
            "unsupported": [204],
        }

    monkeypatch.setattr(cf, "_async_validate_modbus_connection", _ok_connection)
    monkeypatch.setattr(cf, "_async_fetch_device_identity", _identity)
    monkeypatch.setattr(cf, "_async_probe_register_capabilities", _probe)
    # patch out hass-dependent helpers since we don't run under HA
    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    protocol_input = {CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP}
    result2 = await flow.async_step_user(protocol_input)
    assert result2["type"] == "form"
    assert result2["step_id"] == "tcp"
    tcp_schema_keys = {key.schema for key in result2["data_schema"].schema.keys()}
    assert tcp_schema_keys == {CONF_HOST, CONF_PORT, CONF_UNIT}

    tcp_input = {
        CONF_HOST: "1.2.3.4",
        CONF_PORT: 502,
        CONF_UNIT: 17,
    }
    result3 = await flow.async_step_tcp(tcp_input)
    assert result3["type"] == "progress"

    result4 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result4["type"] == "progress_done"

    result5 = await _step_until_not_progress(lambda: flow.async_step_probe_registers())
    assert result5["type"] == "progress_done"

    result6 = await flow.async_step_probe_registers_result()
    assert result6["type"] == "create_entry"
    assert result6["title"] == "Plum Ecovent"
    assert result6["data"][CONF_HOST] == "1.2.3.4"
    assert result6["data"][CONF_PORT] == 502
    assert result6["data"][CONF_UNIT] == 17
    assert result6["data"][CONF_AVAILABLE_REGISTERS] == [201, 202]
    assert result6["data"][CONF_NON_RESPONDING_REGISTERS] == [203]
    assert result6["data"][CONF_UNSUPPORTED_REGISTERS] == [204]
    assert result6["data"][CONF_RESPONDING_REGISTERS] == [201, 202]

    result7 = await flow.async_step_user({CONF_CONNECTION_TYPE: CONNECTION_TYPE_RTU})
    assert result7["type"] == "form"
    assert result7["errors"]["base"] == "rtu_not_supported"

    # invalid port should return form with error
    result8 = await flow.async_step_tcp(
        {CONF_HOST: "1.2.3.4", CONF_PORT: 70000, CONF_UNIT: 1}
    )
    assert result8["type"] == "form"
    assert result8["errors"][CONF_PORT] == "invalid_port"

    # invalid unit should return form with error
    result9 = await flow.async_step_tcp(
        {CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 0}
    )
    assert result9["type"] == "form"
    assert result9["errors"][CONF_UNIT] == "invalid_unit"


@pytest.mark.asyncio
async def test_tcp_flow_verify_adapter_connection_error(monkeypatch):
    """Flow should surface adapter verification errors at verify step."""
    flow = ConfigFlow()
    import custom_components.plum_ecovent.config_flow as cf

    async def _refused_connection(_hass, _config, retries=2, backoff=0.2):
        return "connection_refused"

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_validate_modbus_connection", _refused_connection)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    await flow.async_step_user({CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP})
    result = await flow.async_step_tcp({CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 1})
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

    async def _failing_connection(_hass, _config, retries=2, backoff=0.2):
        return error_code

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_validate_modbus_connection", _failing_connection)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    await flow.async_step_user({CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP})
    result = await flow.async_step_tcp({CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 1})
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

    async def _ok_connection(_hass, _config, retries=2, backoff=0.2):
        return None

    async def _probe_none(_hass, _config, max_attempts=3, deadline_seconds=45.0):
        return {"available": [], "non_responding": [201], "unsupported": []}

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_validate_modbus_connection", _ok_connection)
    monkeypatch.setattr(cf, "_async_probe_register_capabilities", _probe_none)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    await flow.async_step_user({CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP})
    result = await flow.async_step_tcp({CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 1})
    assert result["type"] == "progress"

    result2 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result2["type"] == "progress_done"

    result3 = await _step_until_not_progress(lambda: flow.async_step_probe_registers())
    assert result3["type"] == "progress_done"

    result4 = await flow.async_step_probe_registers_result()
    assert result4["type"] == "form"
    assert result4["step_id"] == "probe_registers"
    assert result4["errors"]["base"] == "probe_failed"


@pytest.mark.asyncio
async def test_tcp_flow_verify_adapter_unit_no_response(monkeypatch):
    """Flow should surface unit_no_response when TCP is reachable but Modbus doesn't reply."""
    flow = ConfigFlow()
    import custom_components.plum_ecovent.config_flow as cf

    async def _unit_no_response(_hass, _config, retries=2, backoff=0.2):
        return "unit_no_response"

    async def _dummy_set_unique_id(*args, **kwargs):
        return None

    monkeypatch.setattr(cf, "_async_validate_modbus_connection", _unit_no_response)
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    await flow.async_step_user({CONF_CONNECTION_TYPE: CONNECTION_TYPE_TCP})
    result = await flow.async_step_tcp({CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 1})
    assert result["type"] == "progress"

    result2 = await _step_until_not_progress(lambda: flow.async_step_verify_adapter())
    assert result2["type"] == "progress_done"

    result3 = await flow.async_step_verify_adapter_result()
    assert result3["type"] == "form"
    assert result3["step_id"] == "verify_adapter"
    assert result3["errors"]["base"] == "unit_no_response"


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
        }
    )
    assert valid["type"] == "create_entry"
    assert valid["data"][CONF_HOST] == "10.0.0.2"
    assert valid["data"][CONF_UNIT] == 7


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
            CONF_OPTIONAL_FORCE_ENABLE: [],
            CONF_OPTIONAL_DISABLE: ["sensor:82:co2"],
        }
    )
    assert valid["type"] == "create_entry"
    assert valid["data"][CONF_OPTIONAL_DISABLE] == ["sensor:82:co2"]


@pytest.mark.asyncio
async def test_probe_capabilities_retry_reclassifies_and_stops(monkeypatch):
    """Probe should reclassify across retries and stop at configured max attempts."""
    import custom_components.plum_ecovent.config_flow as cf

    class SuccessResponse:
        registers = [1]

        @staticmethod
        def isError():
            return False

    class IllegalAddressResponse:
        exception_code = 2

        @staticmethod
        def isError():
            return True

    calls: dict[int, int] = {}
    scripted = {
        10: [None, SuccessResponse()],
        11: [IllegalAddressResponse()],
        12: [None, None, None],
    }

    class FakeManager:
        def __init__(self, hass, config):
            self.retries = 0
            self.backoff = 0.0
            self.timeout = 0.1

        async def async_connect(self):
            return True

        async def async_close(self):
            return None

        async def read_holding_registers(self, address, count, return_error_response=False):
            index = calls.get(int(address), 0)
            calls[int(address)] = index + 1
            plan = scripted[int(address)]
            if index < len(plan):
                return plan[index]
            return plan[-1]

    monkeypatch.setattr(cf, "ModbusClientManager", FakeManager)
    async def _addresses(_hass):
        return [10, 11, 12]

    monkeypatch.setattr(cf, "_async_all_defined_addresses", _addresses)

    result = await cf._async_probe_register_capabilities(None, {}, max_attempts=3, deadline_seconds=5.0)

    assert result["available"] == [10]
    assert result["unsupported"] == [11]
    assert result["non_responding"] == [12]
    assert calls[10] == 2
    assert calls[11] == 1
    assert calls[12] == 3


@pytest.mark.asyncio
async def test_probe_capabilities_respects_deadline(monkeypatch):
    """Probe should stop early on global deadline to avoid startup hangs."""
    import custom_components.plum_ecovent.config_flow as cf

    calls = 0

    class FakeManager:
        def __init__(self, hass, config):
            self.retries = 0
            self.backoff = 0.0
            self.timeout = 0.1

        async def async_connect(self):
            return True

        async def async_close(self):
            return None

        async def read_holding_registers(self, address, count, return_error_response=False):
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.03)
            return None

    monkeypatch.setattr(cf, "ModbusClientManager", FakeManager)
    async def _addresses(_hass):
        return [100, 101, 102, 103, 104]

    monkeypatch.setattr(cf, "_async_all_defined_addresses", _addresses)

    result = await cf._async_probe_register_capabilities(None, {}, max_attempts=3, deadline_seconds=0.05)

    assert result["available"] == []
    assert result["unsupported"] == []
    assert result["non_responding"]
    assert calls < (3 * 5)


@pytest.mark.asyncio
async def test_options_flow_entity_choices_respect_discovery_and_preserve_overrides(monkeypatch):
    """Entity choices should honor discovered availability and hide legacy unavailable override ids."""
    from custom_components.plum_ecovent.config_flow import OptionsFlowHandler
    from types import SimpleNamespace
    import custom_components.plum_ecovent.config_flow as cf

    monkeypatch.setattr(
        cf,
        "entity_catalog",
        lambda: {
            "sensor:82:co2": "sensor · CO2 (82)",
            "sensor:202:outdoor_temperature": "sensor · Outdoor Air Temperature (202)",
            "number:70:supply_fan_speed_g1": "number · Supply Fan Speed Stage 1 (70)",
        },
        raising=False,
    )

    entry = SimpleNamespace(
        data={
            CONF_AVAILABLE_REGISTERS: [82, 202, 70],
        },
        options={
            CONF_OPTIONAL_FORCE_ENABLE: ["sensor:999:legacy_sensor"],
            CONF_OPTIONAL_DISABLE: [],
        },
    )
    flow = OptionsFlowHandler(entry)

    choices = flow._entity_choices()

    assert "sensor:82:co2" in choices
    assert "sensor:202:outdoor_temperature" in choices
    assert "number:70:supply_fan_speed_g1" not in choices
    assert "sensor:999:legacy_sensor" not in choices


@pytest.mark.asyncio
async def test_options_flow_entities_preserve_options_managed_overrides_hidden(monkeypatch):
    """Options-managed number ids stay preserved but hidden from selection choices."""
    from custom_components.plum_ecovent.config_flow import OptionsFlowHandler
    from types import SimpleNamespace

    entry = SimpleNamespace(
        data={CONF_AVAILABLE_REGISTERS: [70]},
        options={
            CONF_OPTIONAL_FORCE_ENABLE: ["number:70:supply_fan_speed_g1"],
            CONF_OPTIONAL_DISABLE: [],
        },
    )
    flow = OptionsFlowHandler(entry)

    choices = flow._entity_choices()
    assert "number:70:supply_fan_speed_g1" not in choices

    result = await flow.async_step_entities(
        {
            CONF_OPTIONAL_FORCE_ENABLE: [],
            CONF_OPTIONAL_DISABLE: [],
        }
    )
    assert result["type"] == "create_entry"
    assert "number:70:supply_fan_speed_g1" in result["data"][CONF_OPTIONAL_FORCE_ENABLE]


@pytest.mark.asyncio
async def test_options_flow_entities_split_enable_disable_choices(monkeypatch):
    """Force-enable should include disabled interactable entities only; disable should include enabled ones."""
    from custom_components.plum_ecovent.config_flow import OptionsFlowHandler
    from types import SimpleNamespace

    entry = SimpleNamespace(
        data={CONF_AVAILABLE_REGISTERS: [82]},
        options={
            CONF_OPTIONAL_FORCE_ENABLE: [],
            CONF_OPTIONAL_DISABLE: ["sensor:82:co2"],
        },
    )
    flow = OptionsFlowHandler(entry)

    force_enable_choices, force_disable_choices = flow._entity_override_choices()

    assert "sensor:82:co2" in force_enable_choices
    assert "sensor:82:co2" not in force_disable_choices


@pytest.mark.asyncio
async def test_options_flow_entities_no_candidates_shows_message(monkeypatch):
    """When no interactable entities are left, entities step should inform the user."""
    from custom_components.plum_ecovent.config_flow import OptionsFlowHandler
    from types import SimpleNamespace

    entry = SimpleNamespace(
        data={},
        options={
            CONF_OPTIONAL_FORCE_ENABLE: [],
            CONF_OPTIONAL_DISABLE: [],
        },
    )
    flow = OptionsFlowHandler(entry)

    monkeypatch.setattr(flow, "_entity_choices", lambda: {})

    result = await flow.async_step_entities()

    assert result["type"] == "form"
    assert result["step_id"] == "entities"
    assert result["errors"]["base"] == "no_entity_override_candidates"
