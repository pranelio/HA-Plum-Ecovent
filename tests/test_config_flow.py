"""Tests for the config flow."""

import sys, os
# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from homeassistant import config_entries
import pytest

from custom_components.plum_ecovent.config_flow import ConfigFlow
from custom_components.plum_ecovent.const import CONF_HOST, CONF_PORT, CONF_UNIT
from homeassistant.const import CONF_NAME


@pytest.mark.asyncio
async def test_tcp_flow():
    """Test that the flow creates an entry with TCP settings.

    We don't have the Home Assistant fixture available, so stub out the
    methods that would normally interact with hass.
    """
    flow = ConfigFlow()
    # patch out hass-dependent helpers since we don't run under HA
    async def _dummy_set_unique_id(*args, **kwargs):
        return None
    flow.async_set_unique_id = _dummy_set_unique_id
    flow._abort_if_unique_id_configured = lambda *args, **kwargs: None

    result = await flow.async_step_user()
    assert result["type"] == "form"

    user_input = {CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 17, CONF_NAME: "My"}
    result2 = await flow.async_step_user(user_input)
    assert result2["type"] == "create_entry"
    assert result2["title"] == "My"
    assert result2["data"][CONF_HOST] == "1.2.3.4"
    assert result2["data"][CONF_PORT] == 502
    assert result2["data"][CONF_UNIT] == 17
