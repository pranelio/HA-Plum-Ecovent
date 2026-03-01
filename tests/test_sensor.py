import asyncio

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
