import asyncio
from custom_components.plum_ecovent.const import REG_SWITCH, REG_NUMBER

class DummyResult:
    def __init__(self, regs):
        self.registers = regs


class DummyManager:
    async def read_holding_registers(self, address, count, unit=1):
        await asyncio.sleep(0)
        return DummyResult([42])


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
    sensor = PlumEcoventSensor(manager, entry)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(sensor.async_update())
        assert sensor.native_value == 42
    finally:
        loop.close()


def test_other_entities():
    # reuse same dynamic import technique for other platforms
    import importlib.util, sys, types

    def load_module(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
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

    manager = DummyManager2()
    entry = SimpleNamespace(title="Test", entry_id="1", data={})

    bina = binary_mod.PlumEcoventBinarySensor(manager, entry)
    sw = switch_mod.PlumEcoventSwitch(manager, entry)
    num = number_mod.PlumEcoventNumber(manager, entry)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(bina.async_update())
        assert bina.is_on is False or bina.is_on is True

        loop.run_until_complete(sw.async_update())
        # update returns bool; ensure property set
        assert sw.is_on in (False, True)

        loop.run_until_complete(sw.async_turn_on())
        assert manager.written[-1] == (REG_SWITCH, 1)
        loop.run_until_complete(sw.async_turn_off())
        assert manager.written[-1] == (REG_SWITCH, 0)

        loop.run_until_complete(num.async_update())
        assert isinstance(num.native_value, (int, float))
        loop.run_until_complete(num.async_set_native_value(5))
        assert manager.written[-1] == (REG_NUMBER, 5)
    finally:
        loop.close()
