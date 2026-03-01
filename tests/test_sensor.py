import asyncio
import sys, os
# ensure custom_components package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class DummyResult:
    def __init__(self, regs):
        self.registers = regs


class DummyManager:
    def __init__(self):
        self.unit = None

    async def read_holding_registers(self, address, count, unit=1):
        # record unit passed
        self.unit = unit
        await asyncio.sleep(0)
        return DummyResult([42])


class DummyCoordinator:
    def __init__(self, data):
        self.data = data
        self.last_update_success = True
        self.update_interval = None

    async def async_request_refresh(self):
        return self


def test_sensor_async_update():
    # Load the sensor module directly to avoid importing the package __init__
    import importlib.util
    spec = importlib.util.spec_from_file_location("custom_components.plum_ecovent.sensor", "custom_components/plum_ecovent/sensor.py")
    mod = importlib.util.module_from_spec(spec)
    # Create package placeholders so relative imports in the module succeed
    import sys, types
    pkg = types.ModuleType('custom_components')
    pkg.__path__ = ['custom_components']
    sys.modules['custom_components'] = pkg
    pkg2 = types.ModuleType('custom_components.plum_ecovent')
    pkg2.__path__ = ['custom_components/plum_ecovent']
    sys.modules['custom_components.plum_ecovent'] = pkg2

    spec.loader.exec_module(mod)
    PlumEcoventSensor = mod.PlumEcoventSensor
    from types import SimpleNamespace

    manager = DummyManager()
    entry = SimpleNamespace(title="Test", entry_id="1", data={})
    # construct with a dummy definition matching old behaviour
    class Def:
        address = 0
        name = "Register 0"
        device_class = None
        unit_of_measurement = None
        accuracy_decimals = None
        entity_category = None
    from custom_components.plum_ecovent.coordinator import build_definition_key

    key = build_definition_key(Def())
    coordinator = DummyCoordinator({key: 42})
    sensor = PlumEcoventSensor(manager, coordinator, entry, Def(), 0)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(sensor.async_update())
        assert sensor.native_value == 42
        assert sensor.available is True
    finally:
        loop.close()




def test_manager_unit_handling():
    """ModbusClientManager should store the unit from config."""

    from custom_components.plum_ecovent.modbus_client import ModbusClientManager
    from custom_components.plum_ecovent.const import CONF_UNIT

    mgr = ModbusClientManager(None, {CONF_UNIT: 5})
    assert mgr.unit == 5
    mgr2 = ModbusClientManager(None, {})
    assert mgr2.unit == 1


def test_other_entities():
    # reuse same dynamic import technique for other platforms
    import importlib.util, sys, types

    def load_module(path, name):
        # load module under the proper package name so relative imports work
        qualname = f"custom_components.plum_ecovent.{name}"
        spec = importlib.util.spec_from_file_location(qualname, path)
        mod = importlib.util.module_from_spec(spec)
        # ensure package context is set
        mod.__package__ = "custom_components.plum_ecovent"
        pkg = types.ModuleType('custom_components')
        pkg.__path__ = ['custom_components']
        sys.modules['custom_components'] = pkg
        pkg2 = types.ModuleType('custom_components.plum_ecovent')
        pkg2.__path__ = ['custom_components/plum_ecovent']
        sys.modules['custom_components.plum_ecovent'] = pkg2
        spec.loader.exec_module(mod)
        return mod

    sensor_mod = load_module('custom_components/plum_ecovent/sensor.py', 'sensor')
    binary_mod = load_module('custom_components/plum_ecovent/binary_sensor.py', 'binary_sensor')
    switch_mod = load_module('custom_components/plum_ecovent/switch.py', 'switch')
    number_mod = load_module('custom_components/plum_ecovent/number.py', 'number')

    from types import SimpleNamespace

    class DummyManager2(DummyManager):
        def __init__(self):
            self.written = []
        async def write_register(self, address, value, unit=1):
            await asyncio.sleep(0)
            self.written.append((address, value))
            return True

    from custom_components.plum_ecovent.coordinator import build_definition_key
    manager = DummyManager2()
    entry = SimpleNamespace(title="Test", entry_id="1", data={})

    # pick one definition from registers for each platform
    from custom_components.plum_ecovent.registers import (
        BINARY_SENSORS,
        SWITCHES,
        NUMBERS,
    )

    binary_def = BINARY_SENSORS[0]
    switch_def = SWITCHES[0]
    number_def = NUMBERS[0]

    coordinator = DummyCoordinator(
        {
            build_definition_key(binary_def): 1,
            build_definition_key(switch_def): switch_def.bitmask,
            build_definition_key(number_def): 4,
        }
    )

    bina = binary_mod.PlumEcoventBinarySensor(manager, coordinator, entry, binary_def)
    sw = switch_mod.PlumEcoventSwitch(manager, coordinator, entry, switch_def)
    num = number_mod.PlumEcoventNumber(manager, coordinator, entry, number_def)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(bina.async_update())
        assert bina.is_on is False or bina.is_on is True

        loop.run_until_complete(sw.async_update())
        # update returns bool; ensure property set
        assert sw.is_on in (False, True)

        loop.run_until_complete(sw.async_turn_on())
        assert manager.written[-1] == (sw._definition.address, 1)
        loop.run_until_complete(sw.async_turn_off())
        assert manager.written[-1] == (sw._definition.address, 0)

        loop.run_until_complete(num.async_update())
        assert isinstance(num.native_value, (int, float))
        loop.run_until_complete(num.async_set_native_value(5))
        assert manager.written[-1] == (num._definition.address, 5)
    finally:
        loop.close()
