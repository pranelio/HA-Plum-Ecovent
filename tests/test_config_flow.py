"""Tests for the config flow."""

from homeassistant import config_entries
import pytest

from custom_components.plum_ecovent.config_flow import ConfigFlow
from custom_components.plum_ecovent.const import CONF_HOST, CONF_PORT, CONF_UNIT, CONF_NAME


@pytest.mark.asyncio
async def test_tcp_flow(hass):
    """Test that the flow creates an entry with TCP settings."""
    flow = ConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()
    assert result["type"] == "form"

    user_input = {CONF_HOST: "1.2.3.4", CONF_PORT: 502, CONF_UNIT: 17, CONF_NAME: "My"}
    result2 = await flow.async_step_user(user_input)
    assert result2["type"] == "create_entry"
    assert result2["title"] == "My"
    assert result2["data"][CONF_HOST] == "1.2.3.4"
    assert result2["data"][CONF_PORT] == 502
    assert result2["data"][CONF_UNIT] == 17
