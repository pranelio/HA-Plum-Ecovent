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
        * ``optional`` – set ``True`` when this register is model-dependent and
            should be probed during discovery.
    """
    address: int
    name: str
    key: Optional[str] = None
    device_class: Optional[str] = None
    entity_category: Optional[str] = None
    skip_updates: Optional[int] = None
    optional: bool = False


BINARY_SENSORS: List[BinarySensorDef] = [
    BinarySensorDef(215, "Ground Heat Exchanger Status", key="heat_exchanger_status", entity_category="diagnostic"),
    BinarySensorDef(217, "Ground Heat Exchanger Regeneration Status", key="heat_exchanger_regeneration", entity_category="diagnostic", skip_updates=5),
    BinarySensorDef(225, "Supply Filter Replacement Required", key="supply_filter_replacement_needed", device_class="problem", entity_category="diagnostic", skip_updates=5),
    BinarySensorDef(228, "Extract Filter Replacement Required", key="extract_filter_replacement_needed", device_class="problem", entity_category="diagnostic", skip_updates=5),
    BinarySensorDef(238, "Secondary Heater Status", key="secondary_heater_status", entity_category="diagnostic", optional=True),
    BinarySensorDef(240, "Secondary Heater Overtemperature Alarm", key="secondary_heater_overtemperature", device_class="problem", entity_category="diagnostic", optional=True),
    BinarySensorDef(242, "Preheater Status", key="preheater_status", entity_category="diagnostic", optional=True),
    BinarySensorDef(244, "Preheater Overtemperature Alarm", key="preheater_overtemperature", device_class="problem", entity_category="diagnostic", optional=True),
    BinarySensorDef(246, "Supply Fan Status", key="supply_fan_status", entity_category="diagnostic"),
    BinarySensorDef(248, "Extract Fan Status", key="extract_fan_status", entity_category="diagnostic"),
]


@dataclass(frozen=True)
class NumberDef:
    """Writable numeric register definition.

    Attributes correspond to Home Assistant ``NumberEntity`` parameters:
    * ``step``/``min_value``/``max_value``/``mode`` control the input widget.
    * ``unit_of_measurement`` and ``device_class`` describe the quantity.
    * ``entity_category`` allows ``config`` or ``diagnostic`` grouping.
        * ``optional`` – set ``True`` when this register is model-dependent and
            should be probed during discovery.
    """
    address: int
    name: str
    key: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    device_class: Optional[str] = None
    entity_category: Optional[str] = None
    step: Optional[Any] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mode: Optional[str] = None
    skip_updates: Optional[int] = None
    optional: bool = False


NUMBERS: List[NumberDef] = [
    NumberDef(70, "Supply Fan Speed Stage 1", key="supply_fan_speed_g1", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(71, "Supply Fan Speed Stage 2", key="supply_fan_speed_g2", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(72, "Supply Fan Speed Stage 3", key="supply_fan_speed_g3", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(74, "Extract Fan Speed Stage 1", key="exhaust_fan_speed_g1", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(75, "Extract Fan Speed Stage 2", key="exhaust_fan_speed_g2", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(76, "Extract Fan Speed Stage 3", key="exhaust_fan_speed_g3", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=3),
    NumberDef(79, "Auto Mode Minimum Fan Speed", key="auto_minimum_fan_speed", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=5),
    NumberDef(80, "Auto Mode Maximum Fan Speed", key="auto_maximum_fan_speed", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=5),
    NumberDef(81, "CO2 Setpoint", key="max_co2", device_class="carbon_dioxide", unit_of_measurement="ppm", entity_category="config", step=1, min_value=0, max_value=2000, mode="BOX", skip_updates=20, optional=True),
    NumberDef(83, "Relative Humidity Setpoint", key="max_humidity", device_class="humidity", unit_of_measurement="%", entity_category="config", step=1, min_value=0, max_value=100, mode="BOX", skip_updates=20, optional=True),
    NumberDef(93, "Comfort Temperature (Day)", key="comfort_temperature_day", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=8, max_value=30, mode="BOX", skip_updates=20),
    NumberDef(94, "Comfort Temperature (Night)", key="comfort_temperature_night", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=8, max_value=30, mode="BOX", skip_updates=20),
    NumberDef(103, "Winter Activation Temperature", key="winter_mode_activation_temperature", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=-20, max_value=20, mode="BOX", skip_updates=20),
    NumberDef(104, "Summer Activation Temperature", key="summer_mode_activation_temperature", device_class="temperature", unit_of_measurement="°C", entity_category="config", step=1, min_value=0, max_value=20, mode="BOX", skip_updates=20),
    NumberDef(115, "Boost 1 Supply Fan Speed", key="boost_supply_speed", unit_of_measurement="%", entity_category="config", step=1, min_value=50, max_value=100, mode="BOX", skip_updates=20),
    NumberDef(116, "Boost 1 Extract Fan Speed", key="boost_extract_speed", unit_of_measurement="%", entity_category="config", step=1, min_value=50, max_value=100, mode="BOX", skip_updates=20),
    NumberDef(117, "Boost 1 Duration", key="boost_duration", device_class="duration", unit_of_measurement="min", entity_category="config", step=1, min_value=1, max_value=60, mode="BOX", skip_updates=20),
    # and so on: additional number definitions can be added here
]


@dataclass(frozen=True)
class SensorDef:
    """Definition for a read‑only numeric register.

    ``filters`` may be a list of conversion dicts applied to the raw value
    (e.g. ``{"multiply": 0.1}`` to divide by ten).  ``accuracy_decimals`` is
    used by the sensor entity to format the value. ``optional`` marks
    model-dependent entities to be probed during discovery.
    """
    address: int
    name: str
    key: Optional[str] = None
    device_class: Optional[str] = None
    unit_of_measurement: Optional[str] = None
    accuracy_decimals: Optional[int] = None
    entity_category: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None
    skip_updates: Optional[int] = None
    optional: bool = False


SENSORS: List[SensorDef] = [
    SensorDef(82, "Indoor CO2", key="co2", device_class="carbon_dioxide", unit_of_measurement="ppm", accuracy_decimals=0, filters=[{"multiply": 0.1}], optional=True),
    SensorDef(84, "Indoor Relative Humidity", key="humidity", device_class="humidity", unit_of_measurement="%", accuracy_decimals=1, filters=[{"multiply": 0.1}], optional=True),
    SensorDef(201, "Comfort Temperature", key="comfort_temperature", device_class="temperature", unit_of_measurement="°C"),
    SensorDef(202, "Outdoor Air Temperature", key="outdoor_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(203, "Leading Air Temperature", key="leading_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(206, "Outdoor Air Temperature (Intake)", key="intake_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(209, "Extract Air Temperature", key="extract_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(208, "Supply Air Temperature", key="supply_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(207, "Exhaust Air Temperature", key="exhaust_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(211, "Control Panel Temperature", key="control_panel_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}]),
    SensorDef(214, "Secondary Heater Downstream Air Temperature", key="secondary_heater_temperature", device_class="temperature", unit_of_measurement="°C", accuracy_decimals=1, filters=[{"multiply": 0.1}], optional=True),
    SensorDef(221, "Operating Days", key="days_of_operation", device_class="duration", unit_of_measurement="d", entity_category="diagnostic"),
    SensorDef(222, "Days Until Service", key="days_to_inspection", device_class="duration", unit_of_measurement="d", entity_category="diagnostic"),
    SensorDef(223, "Days Until Lockout", key="days_until_device_lock", device_class="duration", unit_of_measurement="d", entity_category="diagnostic"),
    SensorDef(230, "Supply Filter Condition", key="supply_filter_pollution", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}], skip_updates=20),
    SensorDef(231, "Supply Filter Operating Days", key="supply_filter_working_days", device_class="duration", unit_of_measurement="d", entity_category="diagnostic", skip_updates=20),
    SensorDef(232, "Extract Filter Condition", key="extract_filter_pollution", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}], skip_updates=20),
    SensorDef(233, "Extract Filter Operating Days", key="extract_filter_working_days", device_class="duration", unit_of_measurement="d", entity_category="diagnostic", skip_updates=20),
    SensorDef(239, "Secondary Heater Current Control", key="secondary_heater_current_control", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}], optional=True),
    SensorDef(243, "Preheater Current Control", key="preheater_current_control", unit_of_measurement="%", entity_category="diagnostic", filters=[{"multiply": 0.1}], optional=True),
    SensorDef(247, "Supply Fan Current Control", key="supply_fan_speed", unit_of_measurement="%"),
    SensorDef(249, "Extract Fan Current Control", key="extract_fan_speed", unit_of_measurement="%"),
]

# switch definitions
@dataclass(frozen=True)
class SwitchDef:
    """On/off register metadata.

    ``bitmask`` allows a single register to expose multiple boolean values.
    ``optional`` marks model-dependent entities to be probed during
    discovery.
    """
    address: int
    name: str
    key: Optional[str] = None
    bitmask: int = 1
    entity_category: Optional[str] = None
    skip_updates: Optional[int] = None
    optional: bool = False


SWITCHES: List[SwitchDef] = [
    SwitchDef(59, "Unit Enable", key="on_off"),
    SwitchDef(78, "Auto Mode", key="auto_mode"),
    SwitchDef(114, "Boost Mode", key="boost_mode"),
    SwitchDef(144, "Secondary Heater Enable", key="secondary_heater", entity_category="config", skip_updates=5, bitmask=0x04, optional=True),
]


def entity_definition_id(platform: str, definition: Any) -> str:
    """Return a stable identifier for an entity definition."""
    return f"{platform}:{int(getattr(definition, 'address', -1))}:{definition_key(definition)}"


def optional_entity_id(platform: str, definition: Any) -> str:
    """Backward-compatible alias for old optional-entity identifier helper."""
    return entity_definition_id(platform, definition)


def entity_catalog() -> dict[str, str]:
    """Return selectable entities mapped by id -> user label."""
    by_platform: dict[str, list[Any]] = {
        "sensor": SENSORS,
        "binary_sensor": BINARY_SENSORS,
        "switch": SWITCHES,
        "number": NUMBERS,
    }

    catalog: dict[str, str] = {}
    for platform, definitions in by_platform.items():
        for definition in definitions:
            entity_id = entity_definition_id(platform, definition)
            catalog[entity_id] = f"{platform} · {definition.name} ({definition.address})"

    return catalog


def optional_entity_catalog() -> dict[str, str]:
    """Return selectable optional entities mapped by id -> user label."""
    catalog: dict[str, str] = {}
    by_platform: dict[str, list[Any]] = {
        "sensor": SENSORS,
        "binary_sensor": BINARY_SENSORS,
        "switch": SWITCHES,
        "number": NUMBERS,
    }
    for platform, definitions in by_platform.items():
        for definition in definitions:
            if not getattr(definition, "optional", False):
                continue
            entity_id = entity_definition_id(platform, definition)
            catalog[entity_id] = f"{platform} · {definition.name} ({definition.address})"

    return catalog


DEVICE_SETTINGS_GROUPS: dict[str, dict[str, Any]] = {
    "supply_fan": {
        "label": "Supply fan speeds",
        "keys": [
            "supply_fan_speed_g1",
            "supply_fan_speed_g2",
            "supply_fan_speed_g3",
        ],
    },
    "exhaust_fan": {
        "label": "Extract fan speeds",
        "keys": [
            "exhaust_fan_speed_g1",
            "exhaust_fan_speed_g2",
            "exhaust_fan_speed_g3",
        ],
    },
    "auto_control": {
        "label": "Auto control",
        "keys": [
            "auto_minimum_fan_speed",
            "auto_maximum_fan_speed",
        ],
    },
    "boost": {
        "label": "Boost settings",
        "keys": [
            "boost_supply_speed",
            "boost_extract_speed",
            "boost_duration",
        ],
    },
    "temperature": {
        "label": "Temperature settings",
        "keys": [
            "comfort_temperature_day",
            "comfort_temperature_night",
            "winter_mode_activation_temperature",
            "summer_mode_activation_temperature",
        ],
    },
}


def definition_key(definition: Any) -> str:
    """Return stable, language-agnostic key for a definition."""
    explicit = getattr(definition, "key", None)
    if explicit:
        return str(explicit)
    name_slug = str(getattr(definition, "name", "unknown")).strip().lower().replace(" ", "_")
    return name_slug


def device_setting_key(definition: NumberDef) -> str:
    """Return a stable options/service key for a configurable number definition."""
    return definition_key(definition)


def device_setting_catalog() -> dict[str, dict[str, Any]]:
    """Return settings map key -> metadata for configurable values managed via options/services."""
    by_key: dict[str, NumberDef] = {device_setting_key(definition): definition for definition in NUMBERS}
    catalog: dict[str, dict[str, Any]] = {}

    for group_id, group_meta in DEVICE_SETTINGS_GROUPS.items():
        for key in group_meta["keys"]:
            definition = by_key.get(key)
            if definition is None:
                continue
            catalog[key] = {
                "key": key,
                "group": group_id,
                "group_label": group_meta["label"],
                "name": definition.name,
                "address": int(definition.address),
                "min": definition.min_value,
                "max": definition.max_value,
                "step": definition.step,
                "unit": definition.unit_of_measurement,
            }

    return catalog


def device_setting_groups() -> dict[str, dict[str, Any]]:
    """Return grouped setting metadata for options flow rendering."""
    catalog = device_setting_catalog()
    grouped: dict[str, dict[str, Any]] = {}
    for group_id, group_meta in DEVICE_SETTINGS_GROUPS.items():
        grouped[group_id] = {
            "label": group_meta["label"],
            "settings": [
                value for value in catalog.values() if value.get("group") == group_id
            ],
        }
    return grouped


def device_setting_addresses() -> set[int]:
    """Return register addresses represented by options-managed device settings."""
    return {int(value["address"]) for value in device_setting_catalog().values()}
