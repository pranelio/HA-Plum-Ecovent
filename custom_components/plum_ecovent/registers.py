"""Register definitions for the Plum Ecovent integration.

Each platform (sensor, binary_sensor, switch, number) iterates over the
appropriate list below when setting up entities.  A definition contains the
Modbus register address and all of the metadata required by Home Assistant
(such as device class, units, or write parameters).  Keep these lists in
sync with the values used by your Plum Ecovent controller; additional
entries can be added as needed.

The dataclasses in this module are frozen to prevent accidental mutation once
entities have been created.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BinarySensorDef:
    """Metadata for a boolean input register.

    * ``address`` – Modbus register to read (holding register).
    * ``name`` – human‑readable entity name.
    * ``device_class`` – optional HA device class (e.g. ``problem``).
    * ``entity_category`` – category such as ``diagnostic`` or ``config``.
    * ``skip_updates`` – only refresh every Nth poll (used for slow-changing
      values).
    """
    address: int
    name: str
    device_class: Optional[str] = None
    entity_category: Optional[str] = None
    skip_updates: Optional[int] = None


BINARY_SENSORS: List[BinarySensorDef] = [
    BinarySensorDef(215, "Heat Exchanger Status", entity_category="diagnostic"),
    BinarySensorDef(217, "Heat Exchanger Regeneration", entity_category="diagnostic", skip_updates=5),
    BinarySensorDef(225, "Supply filter replacement needed", device_class="problem", entity_category="diagnostic", skip_updates=5),
    BinarySensorDef(228, "Extract filter replacement needed", device_class="problem", entity_category="diagnostic", skip_updates=5),
    BinarySensorDef(238, "Secondary Heater Status", entity_category="diagnostic"),
    BinarySensorDef(240, "Secondary Heater Overtemperature", device_class="problem", entity_category="diagnostic"),
    BinarySensorDef(242, "Preheater Status", entity_category="diagnostic"),
    BinarySensorDef(244, "Preheater Overtemperature", device_class="problem", entity_category="diagnostic"),
    BinarySensorDef(246, "Supply Fan Status", entity_category="diagnostic"),
    BinarySensorDef(248, "Extract Fan Status", entity_category="diagnostic"),
]


@dataclass(frozen=True)
class NumberDef:
    """Writable numeric register definition.

    Attributes correspond to Home Assistant ``NumberEntity`` parameters:
    * ``step``/``min_value``/``max_value``/``mode`` control the input widget.
    * ``unit_of_measurement`` and ``device_class`` describe the quantity.
    * ``entity_category`` allows ``config`` or ``diagnostic`` grouping.
    """
    address: int
    name: str
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None
    entity_category: Optional[str] = None
    step: Optional[Any] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mode: Optional[str] = None
    skip_updates: Optional[int] = None


NUMBERS: List[NumberDef] = [
    NumberDef(70, "Supply Fan Speed G1", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(71, "Supply Fan Speed G2", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(72, "Supply Fan Speed G3", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(74, "Exhaust Fan Speed G1", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(75, "Exhaust Fan Speed G2", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(76, "Exhaust Fan Speed G3", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(79, "Auto Minimum Fan Speed", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=5),
    NumberDef(80, "Auto Maximum Fan Speed", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=5),
    NumberDef(81, "Max CO2", device_class="carbon_dioxide", unit_of_measurement="ppm", entity_category="config", step=1, min_value=0, max_value=2000, mode="BOX", skip_updates=20),
    NumberDef(83, "Max Humidity", device_class="humidity", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=20),
    NumberDef(93, "Comfort Temperature Day", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=8, max_value=30, mode="BOX", skip_updates=20),
    NumberDef(94, "Comfort Temperature Night", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=8, max_value=30, mode="BOX", skip_updates=20),
    NumberDef(103, "Winter Mode Activation Temperature", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=-20, max_value=20, mode="BOX", skip_updates=20),
    NumberDef(104, "Summer Mode Activation Temperature", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=0, max_value=20, mode="BOX", skip_updates=20),
    NumberDef(115, "Boost Supply Speed", unit_of_measurement="%", entity_category="config", step=1, min_value=50, max_value=100, mode="BOX", skip_updates=20),
    NumberDef(116, "Boost Extract Speed", unit_of_measurement="%", entity_category="config", step=1, min_value=50, max_value=100, mode="BOX", skip_updates=20),
    NumberDef(117, "Boost Duration", device_class="duration", unit_of_measurement="min", entity_category="config", step=1, min_value=1, max_value=60, mode="BOX", skip_updates=20),
    # and so on: additional number definitions can be added here
]


@dataclass(frozen=True)
class SensorDef:
    """Definition for a read‑only numeric register.

    ``filters`` may be a list of conversion dicts applied to the raw value
    (e.g. ``{"multiply": 0.1}`` to divide by ten).  ``accuracy_decimals`` is
    used by the sensor entity to format the value.
    """
    address: int
    name: str
    device_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    accuracy_decimals: Optional[int] = None
    entity_category: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    skip_updates: Optional[int] = None


SENSORS: List[SensorDef] = [
    SensorDef(82, "CO2", device_class="carbon_dioxide", unit_of_measurement="ppm", accuracy_decimals=0, filters=[{"multiply": 0.1}]),
    SensorDef(84, "Humidity", device_class="humidity", unit_of_measurement="%", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(201, "Comfort Temperature", device_class="temperature", unit_of_measurement="°C"),
    SensorDef(202, "Outdoor Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(203, "Leading Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(206, "Intake Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(209, "Extract Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(208, "Supply Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(207, "Exhaust Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(211, "Control Panel Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(214, "Secondary Heater Temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(221, "Days of operation", device_class="duration", unit_of_measurement="d", entity_category="diagnostic"),
    SensorDef(222, "Days to inspection", device_class="duration", unit_of_measurement="d", entity_category="diagnostic"),
    SensorDef(223, "Days until device lock", device_class="duration", unit_of_measurement="d", entity_category="diagnostic"),
    SensorDef(230, "Supply Filter Pollution", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}], skip_updates=20),
    SensorDef(231, "Supply Filter working days", device_class="duration", unit_of_measurement="d", entity_category="diagnostic", skip_updates=20),
    SensorDef(232, "Extract Filter Pollution", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}], skip_updates=20),
    SensorDef(233, "Extract Filter working days", device_class="duration", unit_of_measurement="d", entity_category="diagnostic", skip_updates=20),
    SensorDef(239, "Secondary Heater current control", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}]),
    SensorDef(243, "Preheater current control", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}]),
    SensorDef(247, "Supply Fan Speed", unit_of_measurement="%"),
    SensorDef(249, "Extract Fan Speed", unit_of_measurement="%"),
    SensorDef(221, "Days of operation", device_class="duration", unit_of_measurement="d", entity_category="diagnostic", filters=None),
    # additional sensors removed for brevity
]

# switch definitions
@dataclass(frozen=True)
class SwitchDef:
    """On/off register metadata.

    ``bitmask`` allows a single register to expose multiple boolean values.
    """
    address: int
    name: str
    bitmask: int = 1
    entity_category: Optional[str] = None
    skip_updates: Optional[int] = None


SWITCHES: List[SwitchDef] = [
    SwitchDef(59, "On⁄Off"),
    SwitchDef(78, "Auto Mode"),
    SwitchDef(114, "Boost Mode"),
    SwitchDef(144, "Secondary Heater", entity_category="config", skip_updates=5, bitmask=0x04),
]
