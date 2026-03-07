import os
import sys
from types import SimpleNamespace

import pytest

# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.plum_ecovent.climate import PlumEcoventClimate
from custom_components.plum_ecovent.coordinator import build_definition_key


class _ReadResponse:
    def __init__(self, value):
        self.registers = [value]


class _DummyManager:
    def __init__(self):
        self.writes: list[tuple[int, int]] = []
        self.reads: list[tuple[int, int]] = []
        self._read_values: dict[int, int] = {
            59: 1,
            69: 2,
            78: 1,
            114: 0,
        }

    async def write_register(self, address, value):
        self.writes.append((int(address), int(value)))
        return True

    async def read_holding_registers(self, address, count):
        self.reads.append((int(address), int(count)))
        value = self._read_values.get(int(address))
        if value is None:
            return None
        return _ReadResponse(value)


class _DummyCoordinator:
    def __init__(self, data):
        self.data = data
        self.refresh_calls = 0

    async def async_request_refresh(self):
        self.refresh_calls += 1


def _definition(address: int, key: str, name: str, min_value=None, max_value=None):
    return SimpleNamespace(
        address=address,
        key=key,
        name=name,
        min_value=min_value,
        max_value=max_value,
    )


@pytest.mark.asyncio
async def test_climate_reads_and_writes_required_registers():
    manager = _DummyManager()

    day_def = _definition(93, "comfort_temperature_day", "Comfort Temperature (Day)", min_value=8, max_value=30)
    night_def = _definition(94, "comfort_temperature_night", "Comfort Temperature (Night)", min_value=8, max_value=30)
    target_humidity_def = _definition(83, "max_humidity", "Relative Humidity Setpoint")
    current_humidity_def = _definition(84, "humidity", "Indoor Relative Humidity")
    current_temp_def = _definition(203, "leading_temperature", "Leading Air Temperature")

    coordinator_values = {
        build_definition_key(current_temp_def): 21.5,
        build_definition_key(day_def): 22,
        build_definition_key(night_def): 20,
        build_definition_key(target_humidity_def): 45,
        build_definition_key(current_humidity_def): 39,
    }
    coordinator = _DummyCoordinator(coordinator_values)

    entry = SimpleNamespace(entry_id="entry123", title="Plum")

    climate = PlumEcoventClimate(
        manager=manager,
        coordinator=coordinator,
        entry=entry,
        day_def=day_def,
        night_def=night_def,
        current_temp_def=current_temp_def,
        target_humidity_def=target_humidity_def,
        current_humidity_def=current_humidity_def,
        device_info=None,
    )

    assert climate._attr_min_temp == 8.0
    assert climate._attr_max_temp == 30.0

    await climate.async_update()
    assert climate._attr_current_temperature == 21.5
    assert climate._attr_target_temperature == 22
    assert climate._attr_current_humidity == 39
    assert climate._attr_target_humidity == 45
    assert climate._attr_hvac_mode == "auto"
    assert climate._attr_fan_mode == "medium"
    assert climate._attr_preset_mode == "none"

    await climate.async_set_temperature(temperature=24)
    assert (93, 24) in manager.writes
    assert (94, 24) in manager.writes

    await climate.async_set_humidity(55)
    assert (83, 55) in manager.writes

    await climate.async_set_hvac_mode("fan_only")
    assert (78, 0) in manager.writes

    await climate.async_set_hvac_mode("auto")
    assert (78, 1) in manager.writes

    await climate.async_set_preset_mode("boost")
    assert (114, 1) in manager.writes

    await climate.async_set_preset_mode("none")
    assert (114, 0) in manager.writes

    await climate.async_set_fan_mode("off")
    assert (59, 0) in manager.writes

    await climate.async_set_fan_mode("high")
    assert (59, 1) in manager.writes
    assert (69, 3) in manager.writes

    assert coordinator.refresh_calls >= 2


@pytest.mark.asyncio
async def test_climate_auto_and_boost_turn_on_unit_when_off():
    manager = _DummyManager()
    manager._read_values[59] = 0

    day_def = _definition(93, "comfort_temperature_day", "Comfort Temperature (Day)", min_value=8, max_value=30)
    night_def = _definition(94, "comfort_temperature_night", "Comfort Temperature (Night)", min_value=8, max_value=30)
    target_humidity_def = _definition(83, "max_humidity", "Relative Humidity Setpoint")
    current_humidity_def = _definition(84, "humidity", "Indoor Relative Humidity")
    current_temp_def = _definition(203, "leading_temperature", "Leading Air Temperature")

    coordinator = _DummyCoordinator({build_definition_key(current_temp_def): 21.0})
    entry = SimpleNamespace(entry_id="entry123", title="Plum")

    climate = PlumEcoventClimate(
        manager=manager,
        coordinator=coordinator,
        entry=entry,
        day_def=day_def,
        night_def=night_def,
        current_temp_def=current_temp_def,
        target_humidity_def=target_humidity_def,
        current_humidity_def=current_humidity_def,
        device_info=None,
    )

    await climate.async_set_hvac_mode("auto")
    assert (59, 1) in manager.writes
    assert (78, 1) in manager.writes

    manager.writes.clear()
    manager._read_values[59] = 0
    await climate.async_set_preset_mode("boost")
    assert (59, 1) in manager.writes
    assert (114, 1) in manager.writes


@pytest.mark.asyncio
async def test_climate_capabilities_disable_unsupported_controls():
    manager = _DummyManager()

    day_def = _definition(93, "comfort_temperature_day", "Comfort Temperature (Day)", min_value=8, max_value=30)
    night_def = _definition(94, "comfort_temperature_night", "Comfort Temperature (Night)", min_value=8, max_value=30)
    current_temp_def = _definition(203, "leading_temperature", "Leading Air Temperature")

    coordinator = _DummyCoordinator({build_definition_key(current_temp_def): 21.0})
    entry = SimpleNamespace(entry_id="entry123", title="Plum")

    climate = PlumEcoventClimate(
        manager=manager,
        coordinator=coordinator,
        entry=entry,
        day_def=day_def,
        night_def=night_def,
        current_temp_def=current_temp_def,
        target_humidity_def=None,
        current_humidity_def=None,
        can_power_unit=False,
        can_control_fan_stage=False,
        can_control_auto_mode=False,
        can_control_boost_mode=False,
        can_set_humidity=False,
        can_read_current_humidity=False,
        device_info=None,
    )

    assert climate._attr_hvac_modes == ["fan_only"]
    assert climate._attr_fan_modes == []
    assert climate._attr_preset_modes == ["none"]
