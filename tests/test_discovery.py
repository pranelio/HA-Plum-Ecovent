import sys, os
from types import SimpleNamespace
from typing import Any, cast

import pytest

# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.plum_ecovent import _async_discover_definitions
from custom_components.plum_ecovent.const import (
    CONF_OPTIONAL_DISABLE,
    CONF_OPTIONAL_FORCE_ENABLE,
    CONF_RESPONDING_REGISTERS,
)


class DummyResponse:
    def __init__(self):
        self.registers = [1]


class DummyManager:
    def __init__(self, reachable_addresses=None):
        self.reachable_addresses = set(reachable_addresses or [])
        self.calls = []

    async def read_holding_registers(self, address, count):
        self.calls.append((address, count))
        if int(address) in self.reachable_addresses:
            return DummyResponse()
        return None


def _definition_id(registers_module, platform, definition):
    return registers_module.entity_definition_id(platform, definition)


@pytest.mark.asyncio
async def test_discovery_uses_responding_registers_snapshot_without_probing():
    """When responding registers are provided, setup should not fallback to probing."""
    from custom_components.plum_ecovent import registers

    # include only a small, predictable subset
    included_addresses = {201, 202, 59}
    manager = DummyManager(reachable_addresses=set())

    discovered = await _async_discover_definitions(
        cast(Any, manager),
        registers,
        {CONF_RESPONDING_REGISTERS: sorted(included_addresses)},
    )

    all_selected = [
        *discovered["sensor"],
        *discovered["binary_sensor"],
        *discovered["switch"],
        *discovered["number"],
    ]
    selected_addresses = {int(definition.address) for definition in all_selected}

    assert selected_addresses == included_addresses
    assert manager.calls == []


@pytest.mark.asyncio
async def test_discovery_overrides_disable_wins_over_force_enable():
    """Disable override must take precedence when the same entity is in both lists."""
    from custom_components.plum_ecovent import registers

    target = registers.SENSORS[0]
    entity_id = _definition_id(registers, "sensor", target)

    manager = DummyManager(reachable_addresses={int(target.address)})
    discovered = await _async_discover_definitions(
        cast(Any, manager),
        registers,
        {
            CONF_RESPONDING_REGISTERS: [int(target.address)],
            CONF_OPTIONAL_FORCE_ENABLE: [entity_id],
            CONF_OPTIONAL_DISABLE: [entity_id],
        },
    )

    sensor_ids = {
        _definition_id(registers, "sensor", definition) for definition in discovered["sensor"]
    }
    assert entity_id not in sensor_ids


@pytest.mark.asyncio
async def test_discovery_legacy_fallback_probes_when_snapshot_missing():
    """Legacy entries without responding snapshot should probe and include reachable entities."""
    from custom_components.plum_ecovent import registers

    sensor = registers.SENSORS[1]
    switch = registers.SWITCHES[0]
    reachable = {int(sensor.address), int(switch.address)}

    manager = DummyManager(reachable_addresses=reachable)
    discovered = await _async_discover_definitions(cast(Any, manager), registers, {})

    selected_addresses = {
        int(definition.address)
        for definition in [
            *discovered["sensor"],
            *discovered["binary_sensor"],
            *discovered["switch"],
            *discovered["number"],
        ]
    }

    assert reachable.issubset(selected_addresses)
    assert manager.calls, "Expected probe calls when responding snapshot is absent"


@pytest.mark.asyncio
async def test_discovery_empty_snapshot_skips_fallback_probing():
    """When available snapshot is explicitly empty, discovery should not probe or create entities."""
    from custom_components.plum_ecovent import registers
    from custom_components.plum_ecovent.const import CONF_AVAILABLE_REGISTERS

    manager = DummyManager(reachable_addresses={201, 202, 59})
    discovered = await _async_discover_definitions(
        cast(Any, manager),
        registers,
        {CONF_AVAILABLE_REGISTERS: []},
    )

    all_selected = [
        *discovered["sensor"],
        *discovered["binary_sensor"],
        *discovered["switch"],
        *discovered["number"],
    ]

    assert all_selected == []
    assert manager.calls == []
