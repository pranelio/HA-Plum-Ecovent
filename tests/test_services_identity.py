import sys, os
from types import SimpleNamespace
from typing import Any, cast

import pytest

# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.plum_ecovent import _async_refresh_device_identity_once, _async_register_services
from custom_components.plum_ecovent.const import (
    CONF_DEVICE_INFO_FETCH_ATTEMPTED,
    CONF_DEVICE_INFO_PENDING_FETCH,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SERIAL,
    CONF_FIRMWARE_VERSION,
    DOMAIN,
)


class FakeServices:
    def __init__(self):
        self._handlers = {}

    def has_service(self, domain, service):
        return (domain, service) in self._handlers

    def async_register(self, domain, service, handler, schema=None):
        self._handlers[(domain, service)] = {
            "handler": handler,
            "schema": schema,
        }

    def async_remove(self, domain, service):
        self._handlers.pop((domain, service), None)

    def get_handler(self, domain, service):
        return self._handlers[(domain, service)]["handler"]


class DummyManager:
    def __init__(self, write_ok=True):
        self.write_ok = write_ok
        self.writes = []

    async def write_register(self, address, value):
        self.writes.append((address, value))
        return self.write_ok


class DummyCoordinator:
    def __init__(self):
        self.refresh_calls = 0

    async def async_request_refresh(self):
        self.refresh_calls += 1


def _pick_setting():
    from custom_components.plum_ecovent.registers import device_setting_catalog

    key, meta = next(iter(device_setting_catalog().items()))
    min_value = meta.get("min")
    max_value = meta.get("max")
    if min_value is not None:
        valid = int(min_value)
        invalid = int(min_value) - 1
    elif max_value is not None:
        valid = int(max_value)
        invalid = int(max_value) + 1
    else:
        valid = 1
        invalid = 10_000
    return key, meta, valid, invalid


@pytest.mark.asyncio
async def test_set_device_setting_service_success_single_entry():
    key, meta, valid_value, _invalid = _pick_setting()

    manager = DummyManager(write_ok=True)
    coordinator = DummyCoordinator()
    hass = SimpleNamespace(
        services=FakeServices(),
        data={DOMAIN: {"entry_1": {"manager": manager, "coordinator": coordinator}}},
    )

    await _async_register_services(cast(Any, hass))
    handler = hass.services.get_handler(DOMAIN, "set_device_setting")
    await handler(SimpleNamespace(data={"setting": key, "value": valid_value}))

    assert manager.writes == [(int(meta["address"]), int(valid_value))]
    assert coordinator.refresh_calls == 1


@pytest.mark.asyncio
async def test_set_device_setting_service_rejects_unknown_key():
    manager = DummyManager(write_ok=True)
    hass = SimpleNamespace(
        services=FakeServices(),
        data={DOMAIN: {"entry_1": {"manager": manager, "coordinator": None}}},
    )

    await _async_register_services(cast(Any, hass))
    handler = hass.services.get_handler(DOMAIN, "set_device_setting")

    with pytest.raises(ValueError, match="Unknown setting key"):
        await handler(SimpleNamespace(data={"setting": "does_not_exist", "value": 1}))


@pytest.mark.asyncio
async def test_set_device_setting_service_rejects_out_of_range_value():
    key, _meta, _valid_value, invalid_value = _pick_setting()
    manager = DummyManager(write_ok=True)
    hass = SimpleNamespace(
        services=FakeServices(),
        data={DOMAIN: {"entry_1": {"manager": manager, "coordinator": None}}},
    )

    await _async_register_services(cast(Any, hass))
    handler = hass.services.get_handler(DOMAIN, "set_device_setting")

    with pytest.raises(ValueError):
        await handler(SimpleNamespace(data={"setting": key, "value": invalid_value}))


@pytest.mark.asyncio
async def test_set_device_setting_service_requires_entry_id_when_multiple_entries():
    key, _meta, valid_value, _invalid = _pick_setting()
    hass = SimpleNamespace(
        services=FakeServices(),
        data={
            DOMAIN: {
                "entry_1": {"manager": DummyManager(), "coordinator": None},
                "entry_2": {"manager": DummyManager(), "coordinator": None},
            }
        },
    )

    await _async_register_services(cast(Any, hass))
    handler = hass.services.get_handler(DOMAIN, "set_device_setting")

    with pytest.raises(ValueError, match="Provide entry_id"):
        await handler(SimpleNamespace(data={"setting": key, "value": valid_value}))


@pytest.mark.asyncio
async def test_set_device_setting_service_rejects_unknown_entry_id():
    key, _meta, valid_value, _invalid = _pick_setting()
    hass = SimpleNamespace(
        services=FakeServices(),
        data={DOMAIN: {"entry_1": {"manager": DummyManager(), "coordinator": None}}},
    )

    await _async_register_services(cast(Any, hass))
    handler = hass.services.get_handler(DOMAIN, "set_device_setting")

    with pytest.raises(ValueError, match="Entry not loaded"):
        await handler(
            SimpleNamespace(data={"entry_id": "missing", "setting": key, "value": valid_value})
        )


@pytest.mark.asyncio
async def test_set_device_setting_service_write_failure_raises_error():
    key, _meta, valid_value, _invalid = _pick_setting()
    manager = DummyManager(write_ok=False)
    hass = SimpleNamespace(
        services=FakeServices(),
        data={DOMAIN: {"entry_1": {"manager": manager, "coordinator": None}}},
    )

    await _async_register_services(cast(Any, hass))
    handler = hass.services.get_handler(DOMAIN, "set_device_setting")

    with pytest.raises(ValueError, match="Failed to write register"):
        await handler(SimpleNamespace(data={"setting": key, "value": valid_value}))


@pytest.mark.asyncio
async def test_refresh_identity_once_updates_entry(monkeypatch):
    updates = []

    async def _identity(_manager):
        return {
            CONF_DEVICE_NAME: "Ecovent X",
            CONF_DEVICE_SERIAL: "ABC123",
            CONF_FIRMWARE_VERSION: "1.2.3",
        }

    monkeypatch.setitem(
        _async_refresh_device_identity_once.__globals__, "_async_read_device_identity", _identity
    )

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_update_entry=lambda entry, data: updates.append((entry, data))
        )
    )
    entry = SimpleNamespace(entry_id="entry_1")

    result = await _async_refresh_device_identity_once(
        cast(Any, hass), cast(Any, entry), cast(Any, SimpleNamespace()), {}
    )
    assert result is not None
    assert result[CONF_DEVICE_NAME] == "Ecovent X"
    assert result[CONF_DEVICE_SERIAL] == "ABC123"
    assert result[CONF_FIRMWARE_VERSION] == "1.2.3"
    assert result[CONF_DEVICE_INFO_PENDING_FETCH] is False
    assert result[CONF_DEVICE_INFO_FETCH_ATTEMPTED] is True
    assert len(updates) == 1


@pytest.mark.asyncio
async def test_refresh_identity_once_skips_if_already_attempted(monkeypatch):
    called = {"count": 0}

    async def _identity(_manager):
        called["count"] += 1
        return {}

    monkeypatch.setitem(
        _async_refresh_device_identity_once.__globals__, "_async_read_device_identity", _identity
    )

    hass = SimpleNamespace(config_entries=SimpleNamespace(async_update_entry=lambda *args, **kwargs: None))
    entry = SimpleNamespace(entry_id="entry_1")
    entry_data = {
        CONF_DEVICE_INFO_PENDING_FETCH: True,
        CONF_DEVICE_INFO_FETCH_ATTEMPTED: True,
    }

    result = await _async_refresh_device_identity_once(
        cast(Any, hass), cast(Any, entry), cast(Any, SimpleNamespace()), entry_data
    )
    assert result is None
    assert called["count"] == 0


@pytest.mark.asyncio
async def test_refresh_identity_once_pending_retry_forces_attempt(monkeypatch):
    called = {"count": 0}

    async def _identity(_manager):
        called["count"] += 1
        return {}

    monkeypatch.setitem(
        _async_refresh_device_identity_once.__globals__, "_async_read_device_identity", _identity
    )

    hass = SimpleNamespace(config_entries=SimpleNamespace(async_update_entry=lambda *args, **kwargs: None))
    entry = SimpleNamespace(entry_id="entry_1")
    entry_data = {
        CONF_DEVICE_NAME: "Ecovent",
        CONF_DEVICE_SERIAL: "S123",
        CONF_FIRMWARE_VERSION: "1.0",
        CONF_DEVICE_INFO_PENDING_FETCH: True,
        CONF_DEVICE_INFO_FETCH_ATTEMPTED: False,
    }

    result = await _async_refresh_device_identity_once(
        cast(Any, hass), cast(Any, entry), cast(Any, SimpleNamespace()), entry_data
    )
    assert result is not None
    assert result[CONF_DEVICE_INFO_PENDING_FETCH] is False
    assert result[CONF_DEVICE_INFO_FETCH_ATTEMPTED] is True
    assert called["count"] == 1
