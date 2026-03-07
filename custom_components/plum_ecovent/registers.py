"""Register metadata loaded from the canonical YAML register map.

Single source of truth:
- vendor register map + semantics: custom_components/plum_ecovent/plum_modbus_register_map.yaml
- integration entity metadata (platform mapping, keys, filters, groups, icons):
    plum_modbus_register_map.yaml -> integration.entities
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


_PACKAGED_REGISTER_MAP_PATH = Path(__file__).resolve().parent / "plum_modbus_register_map.yaml"


@dataclass(frozen=True)
class BinarySensorDef:
    address: int
    name: str
    key: Optional[str] = None
    device_class: Optional[str] = None
    entity_category: Optional[str] = None
    skip_updates: Optional[int] = None
    optional: bool = False
    icon: Optional[str] = None
    groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class NumberDef:
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
    icon: Optional[str] = None
    groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class SensorDef:
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
    icon: Optional[str] = None
    groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class SwitchDef:
    address: int
    name: str
    key: Optional[str] = None
    bitmask: int = 1
    entity_category: Optional[str] = None
    skip_updates: Optional[int] = None
    optional: bool = False
    icon: Optional[str] = None
    groups: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def _load_register_map() -> dict[str, Any]:
    if not _PACKAGED_REGISTER_MAP_PATH.exists():
        raise FileNotFoundError(
            "Register map YAML not found: "
            f"{_PACKAGED_REGISTER_MAP_PATH}"
        )

    with _PACKAGED_REGISTER_MAP_PATH.open("r", encoding="utf-8") as file_handle:
        parsed = yaml.safe_load(file_handle) or {}
    if not isinstance(parsed, dict):
        raise ValueError("Invalid register map format: expected top-level mapping")
    return parsed


@lru_cache(maxsize=1)
def _canonical_registers_by_name() -> dict[str, dict[str, Any]]:
    registers = _load_register_map().get("registers", [])
    if not isinstance(registers, list):
        return {}
    by_name: dict[str, dict[str, Any]] = {}
    for entry in registers:
        if not isinstance(entry, dict):
            continue
        raw_name = entry.get("name")
        if raw_name is None:
            continue
        by_name[str(raw_name)] = entry
    return by_name


def _canonical_unit_to_ha(unit: Any) -> Optional[str]:
    if unit is None:
        return None
    normalized = str(unit).strip().lower()
    unit_map = {
        "percent": "%",
        "celsius": "°C",
        "ppm": "ppm",
    }
    return unit_map.get(normalized, str(unit))


def _merge_entity_with_canonical_register(item: dict[str, Any]) -> dict[str, Any]:
    merged = dict(item)
    register_name = merged.get("register")
    canonical: dict[str, Any] | None = None

    if register_name is not None:
        canonical = _canonical_registers_by_name().get(str(register_name))
        if canonical is None:
            raise ValueError(f"Unknown canonical register reference: {register_name}")

    if canonical is not None:
        canonical_address = canonical.get("address")
        if canonical_address is None:
            raise ValueError(f"Canonical register {register_name} has no address")

        explicit_address = merged.get("address")
        if explicit_address is not None and int(explicit_address) != int(canonical_address):
            raise ValueError(
                "Integration entity address mismatch for register "
                f"{register_name}: {explicit_address} != {canonical_address}"
            )

        merged.setdefault("address", int(canonical_address))

        platform = str(merged.get("platform", ""))
        unit = _canonical_unit_to_ha(canonical.get("unit"))
        if unit and platform in {"sensor", "number"}:
            merged.setdefault("unit_of_measurement", unit)

        if platform == "number":
            if canonical.get("min") is not None:
                merged.setdefault("min_value", canonical.get("min"))
            if canonical.get("max") is not None:
                merged.setdefault("max_value", canonical.get("max"))

    if merged.get("address") is None:
        raise ValueError("Integration entity is missing address/register reference")

    return merged


@lru_cache(maxsize=1)
def _integration_entities() -> list[dict[str, Any]]:
    data = _load_register_map().get("integration", {})
    if not isinstance(data, dict):
        return []
    entities = data.get("entities", [])
    if not isinstance(entities, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in entities:
        if isinstance(item, dict):
            normalized.append(_merge_entity_with_canonical_register(item))
    return normalized


def _groups_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    return ()


def _as_int(value: Any) -> int:
    return int(value)


def _defs_for_platform(platform: str) -> list[dict[str, Any]]:
    return [item for item in _integration_entities() if str(item.get("platform", "")) == platform]


def _build_sensor_def(item: dict[str, Any]) -> SensorDef:
    filters = item.get("filters")
    if not isinstance(filters, list):
        filters = None
    return SensorDef(
        address=_as_int(item["address"]),
        name=str(item["name"]),
        key=item.get("key"),
        device_class=item.get("device_class"),
        unit_of_measurement=item.get("unit_of_measurement"),
        accuracy_decimals=item.get("accuracy_decimals"),
        entity_category=item.get("entity_category"),
        filters=filters,
        skip_updates=item.get("skip_updates"),
        optional=bool(item.get("optional", False)),
        icon=item.get("icon"),
        groups=_groups_tuple(item.get("groups")),
    )


def _build_binary_sensor_def(item: dict[str, Any]) -> BinarySensorDef:
    return BinarySensorDef(
        address=_as_int(item["address"]),
        name=str(item["name"]),
        key=item.get("key"),
        device_class=item.get("device_class"),
        entity_category=item.get("entity_category"),
        skip_updates=item.get("skip_updates"),
        optional=bool(item.get("optional", False)),
        icon=item.get("icon"),
        groups=_groups_tuple(item.get("groups")),
    )


def _build_switch_def(item: dict[str, Any]) -> SwitchDef:
    return SwitchDef(
        address=_as_int(item["address"]),
        name=str(item["name"]),
        key=item.get("key"),
        bitmask=int(item.get("bitmask", 1)),
        entity_category=item.get("entity_category"),
        skip_updates=item.get("skip_updates"),
        optional=bool(item.get("optional", False)),
        icon=item.get("icon"),
        groups=_groups_tuple(item.get("groups")),
    )


def _build_number_def(item: dict[str, Any]) -> NumberDef:
    return NumberDef(
        address=_as_int(item["address"]),
        name=str(item["name"]),
        key=item.get("key"),
        unit_of_measurement=item.get("unit_of_measurement"),
        device_class=item.get("device_class"),
        entity_category=item.get("entity_category"),
        step=item.get("step"),
        min_value=item.get("min_value"),
        max_value=item.get("max_value"),
        mode=item.get("mode"),
        skip_updates=item.get("skip_updates"),
        optional=bool(item.get("optional", False)),
        icon=item.get("icon"),
        groups=_groups_tuple(item.get("groups")),
    )


SENSORS: List[SensorDef] = [_build_sensor_def(item) for item in _defs_for_platform("sensor")]
BINARY_SENSORS: List[BinarySensorDef] = [
    _build_binary_sensor_def(item) for item in _defs_for_platform("binary_sensor")
]
SWITCHES: List[SwitchDef] = [_build_switch_def(item) for item in _defs_for_platform("switch")]
NUMBERS: List[NumberDef] = [_build_number_def(item) for item in _defs_for_platform("number")]


def definition_key(definition: Any) -> str:
    explicit = getattr(definition, "key", None)
    if explicit:
        return str(explicit)
    return str(getattr(definition, "name", "unknown")).strip().lower().replace(" ", "_")


def entity_definition_id(platform: str, definition: Any) -> str:
    return f"{platform}:{int(getattr(definition, 'address', -1))}:{definition_key(definition)}"


def optional_entity_id(platform: str, definition: Any) -> str:
    return entity_definition_id(platform, definition)


def _platform_map() -> dict[str, list[Any]]:
    return {
        "sensor": SENSORS,
        "binary_sensor": BINARY_SENSORS,
        "switch": SWITCHES,
        "number": NUMBERS,
    }


def entity_catalog() -> dict[str, str]:
    catalog: dict[str, str] = {}
    for platform, definitions in _platform_map().items():
        for definition in definitions:
            entity_id = entity_definition_id(platform, definition)
            catalog[entity_id] = f"{platform} · {definition.name} ({definition.address})"
    return catalog


def optional_entity_catalog() -> dict[str, str]:
    catalog: dict[str, str] = {}
    for platform, definitions in _platform_map().items():
        for definition in definitions:
            if not getattr(definition, "optional", False):
                continue
            entity_id = entity_definition_id(platform, definition)
            catalog[entity_id] = f"{platform} · {definition.name} ({definition.address})"
    return catalog


def entity_definitions_for_group(group: str, platform: str | None = None) -> list[Any]:
    group_name = str(group)
    result: list[Any] = []
    platforms = _platform_map()
    selected: Iterable[tuple[str, list[Any]]]
    if platform is None:
        selected = platforms.items()
    else:
        selected = [(platform, platforms.get(platform, []))]
    for _, definitions in selected:
        for definition in definitions:
            if group_name in getattr(definition, "groups", ()): 
                result.append(definition)
    return result


def grouped_entity_catalog() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for platform, definitions in _platform_map().items():
        for definition in definitions:
            entity_id = entity_definition_id(platform, definition)
            for group_name in getattr(definition, "groups", ()): 
                grouped.setdefault(str(group_name), []).append(entity_id)
    return {key: sorted(value) for key, value in grouped.items()}


@lru_cache(maxsize=1)
def _device_settings_groups_raw() -> dict[str, dict[str, Any]]:
    integration = _load_register_map().get("integration", {})
    if not isinstance(integration, dict):
        return {}
    groups = integration.get("device_settings_groups", {})
    if not isinstance(groups, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for group_id, group_meta in groups.items():
        if not isinstance(group_meta, dict):
            continue
        keys = group_meta.get("keys", [])
        normalized[str(group_id)] = {
            "label": str(group_meta.get("label", group_id)),
            "keys": [str(key) for key in keys] if isinstance(keys, list) else [],
        }
    return normalized


def device_setting_key(definition: NumberDef) -> str:
    return definition_key(definition)


def device_setting_catalog() -> dict[str, dict[str, Any]]:
    by_key: dict[str, NumberDef] = {device_setting_key(definition): definition for definition in NUMBERS}
    catalog: dict[str, dict[str, Any]] = {}
    for group_id, group_meta in _device_settings_groups_raw().items():
        keys = group_meta.get("keys", [])
        for key in keys:
            definition = by_key.get(str(key))
            if definition is None:
                continue
            catalog[str(key)] = {
                "key": str(key),
                "group": group_id,
                "group_label": group_meta.get("label", group_id),
                "name": definition.name,
                "address": int(definition.address),
                "min": definition.min_value,
                "max": definition.max_value,
                "step": definition.step,
                "unit": definition.unit_of_measurement,
            }
    return catalog


def device_setting_groups() -> dict[str, dict[str, Any]]:
    catalog = device_setting_catalog()
    grouped: dict[str, dict[str, Any]] = {}
    for group_id, group_meta in _device_settings_groups_raw().items():
        grouped[group_id] = {
            "label": group_meta["label"],
            "settings": [
                value for value in catalog.values() if value.get("group") == group_id
            ],
        }
    return grouped


def device_setting_addresses() -> set[int]:
    return {int(value["address"]) for value in device_setting_catalog().values()}
