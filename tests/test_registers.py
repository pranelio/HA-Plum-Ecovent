import sys
import os
import re
from pathlib import Path

import yaml

# make repo root available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from custom_components.plum_ecovent import registers


def test_all_loaded_definitions_have_resolved_addresses() -> None:
    for definition in [
        *registers.SENSORS,
        *registers.BINARY_SENSORS,
        *registers.SWITCHES,
        *registers.NUMBERS,
    ]:
        assert isinstance(definition.address, int)
        assert definition.address >= 0


def test_number_metadata_inherits_from_canonical_register() -> None:
    co2_setpoint = next(definition for definition in registers.NUMBERS if definition.key == "max_co2")

    assert co2_setpoint.address == 81
    assert co2_setpoint.unit_of_measurement == "ppm"
    assert co2_setpoint.min_value == 0
    assert co2_setpoint.max_value == 2000


def test_sensor_unit_inherits_from_canonical_register() -> None:
    co2_sensor = next(definition for definition in registers.SENSORS if definition.key == "co2")

    assert co2_sensor.address == 82
    assert co2_sensor.unit_of_measurement == "ppm"


def _canonical_display_mapping_from_conventions() -> dict[str, str]:
    content = Path("docs/hvac_naming_conventions.md").read_text(encoding="utf-8")
    mapping: dict[str, str] = {}
    in_table = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Vendor register-map key | Canonical display name |"):
            in_table = True
            continue

        if in_table:
            if not stripped.startswith("|"):
                break
            if stripped.startswith("|---"):
                continue

            parts = [part.strip() for part in stripped.strip("|").split("|")]
            if len(parts) < 2:
                continue

            register_name = parts[0]
            canonical_name = parts[1]
            canonical_name = re.sub(r"\*\([^)]*\)\*", "", canonical_name)
            canonical_name = canonical_name.replace("`", "").strip()
            if register_name:
                mapping[register_name] = canonical_name

    return mapping


def test_integration_entity_names_follow_canonical_english_baseline() -> None:
    """YAML runtime names should follow canonical baseline naming.

    This check validates canonical EN names in `integration.entities` only.
    UI localization for other languages should be handled via translations,
    not by changing runtime keys/structure.
    """
    register_map = yaml.safe_load(Path("docs/plum_modbus_register_map.yaml").read_text(encoding="utf-8"))
    entities = register_map.get("integration", {}).get("entities", [])

    mapping = _canonical_display_mapping_from_conventions()
    assert mapping, "No canonical mapping parsed from docs/hvac_naming_conventions.md"

    mismatches: list[tuple[str, str, str]] = []
    missing: list[str] = []
    for entity in entities:
        register_name = entity.get("register")
        display_name = entity.get("name")
        if not register_name or not display_name:
            continue

        expected = mapping.get(str(register_name))
        if expected is None:
            missing.append(str(register_name))
            continue

        if str(display_name).strip() != str(expected).strip():
            mismatches.append((str(register_name), str(expected), str(display_name)))

    assert not missing, f"Missing canonical mapping entries for registers: {sorted(set(missing))}"
    assert not mismatches, f"Canonical naming mismatches: {mismatches}"
