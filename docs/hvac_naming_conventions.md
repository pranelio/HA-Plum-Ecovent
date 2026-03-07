# HVAC Naming Conventions for Plum Ecovent

## 1) Purpose

This document defines **canonical, industry-standard HVAC naming** for air streams,
measurements, and controls used by this integration.

Use these terms as the target vocabulary when normalizing register/entity names.
The goal is to reduce clutter and ambiguity caused by inconsistent vendor wording.

## 2) Canonical airflow terms

Use the following meanings consistently:

- **Outdoor Air (OA)**: air entering the unit from outside.
- **Supply Air (SA)**: conditioned air delivered from the unit to indoor spaces.
- **Extract Air (EA)**: air removed from indoor spaces and returned to the unit.
- **Exhaust Air (EXH)**: air discharged by the unit to outside.
- **Recirculated Air (RA/REC)**: indoor air recirculated without full outdoor exchange (if present).

### 2.1 Air-side path reference

Typical HRV/ERV path:

- OA -> heat exchanger -> SA
- EA -> heat exchanger -> EXH

## 3) Canonical point names (preferred)

### 3.1 Temperatures

- `Outdoor Air Temperature`
- `Supply Air Temperature`
- `Extract Air Temperature`
- `Exhaust Air Temperature`
- `Control Panel Temperature` (for local controller temp)
- `Comfort Temperature`

### 3.2 Fan-related

- `Supply Fan Speed`
- `Extract Fan Speed`
- `Supply Fan Status`
- `Extract Fan Status`

For staged targets:

- `Supply Fan Speed Stage 1/2/3`
- `Extract Fan Speed Stage 1/2/3`

### 3.3 Air quality and humidity

- `Indoor CO2`
- `Indoor Relative Humidity`
- `CO2 Setpoint`
- `Relative Humidity Setpoint`

### 3.4 Filters and diagnostics

- `Supply Filter Condition`
- `Extract Filter Condition`
- `Supply Filter Replacement Required`
- `Extract Filter Replacement Required`
- `Operating Days`
- `Days Until Service`

### 3.5 Modes and control

- `Auto Mode`
- `Boost Mode`
- `Boost Duration`
- `Secondary Heater Enable`
- `Preheater Status`

## 4) Mapping from current/vendor terms

This table defines recommended renames to canonical terms.

| Current / vendor-like term | Canonical term |
|---|---|
| Leading Temperature | Supply Air Temperature *(or keep as `Leading Air Temperature` if hardware semantics differ)* |
| Intake Temperature | Outdoor Air Temperature |
| Extract Temperature | Extract Air Temperature |
| Exhaust Temperature | Exhaust Air Temperature |
| Supply Temperature | Supply Air Temperature |
| Comfort Temperature Day | Comfort Temperature (Day) |
| Comfort Temperature Night | Comfort Temperature (Night) |
| Supply Fan Speed G1/G2/G3 | Supply Fan Speed Stage 1/2/3 |
| Exhaust Fan Speed G1/G2/G3 | Extract Fan Speed Stage 1/2/3 |
| Max Humidity | Relative Humidity Setpoint |
| Max CO2 | CO2 Setpoint |
| Days to inspection | Days Until Service |
| Days until device lock | Days Until Lockout |

## 4.1 Register-map key mapping (vendor -> canonical)

The following extends the mapping using vendor keys from `docs/plum_modbus_register_map.yaml`.
Use these as canonical UI labels (entities, options, services, diagnostics).

| Vendor register-map key | Canonical display name |
|---|---|
| unit_on_off | Unit Enable |
| gear_schedule_enable | Fan Stage Schedule Enable |
| gear_schedule_day | Fan Stage Schedule Day |
| gear_schedule_interval | Fan Stage Schedule Interval |
| gear_schedule_start_hour | Fan Stage Schedule Start Hour |
| gear_schedule_start_minute_halfhour | Fan Stage Schedule Start Minute |
| gear_schedule_end_hour | Fan Stage Schedule End Hour |
| gear_schedule_end_minute_halfhour | Fan Stage Schedule End Minute |
| gear_schedule_mode | Fan Stage Schedule Mode |
| gear_schedule_copy_days_mask | Fan Stage Schedule Copy Days |
| unit_operation_mode | Unit Operating Mode |
| supply_fan_speed_gear1 | Supply Fan Speed Stage 1 |
| supply_fan_speed_gear2 | Supply Fan Speed Stage 2 |
| supply_fan_speed_gear3 | Supply Fan Speed Stage 3 |
| extract_fan_speed_gear1 | Extract Fan Speed Stage 1 |
| extract_fan_speed_gear2 | Extract Fan Speed Stage 2 |
| extract_fan_speed_gear3 | Extract Fan Speed Stage 3 |
| auto_mode_enable | Auto Mode Enable |
| auto_mode_min_fan_speed | Auto Mode Minimum Fan Speed |
| auto_mode_max_fan_speed | Auto Mode Maximum Fan Speed |
| auto_mode_co2_setpoint | CO2 Setpoint |
| co2_current | Indoor CO2 |
| auto_mode_rh_setpoint | Relative Humidity Setpoint |
| rh_current | Indoor Relative Humidity |
| time_mode | Timed Ventilation Mode |
| away_duration_hours | Away Mode Duration |
| party_duration_hours | Party Mode Duration |
| airing_duration_minutes | Airing Mode Duration |
| exhaust_fan_speed_ventilation_mode | Extract Fan Speed (Ventilation Mode) |
| fireplace_mode | Fireplace Mode Enable |
| fireplace_fan_difference | Fireplace Mode Fan Delta |
| temperature_schedule_selection | Comfort Temperature Schedule Selector |
| comfort_temperature_day | Comfort Temperature (Day) |
| comfort_temperature_night | Comfort Temperature (Night) |
| temperature_schedule_day | Temperature Schedule Day |
| temperature_schedule_start_hour | Temperature Schedule Start Hour |
| temperature_schedule_start_minute_halfhour | Temperature Schedule Start Minute |
| temperature_schedule_end_hour | Temperature Schedule End Hour |
| temperature_schedule_end_minute_halfhour | Temperature Schedule End Minute |
| temperature_interval_mode | Temperature Schedule Interval Mode |
| temperature_schedule_copy_days_mask | Temperature Schedule Copy Days |
| seasonal_mode | Seasonal Mode |
| winter_activation_temperature | Winter Activation Temperature |
| summer_activation_temperature | Summer Activation Temperature |
| zone_schedule_enable | Zone Schedule Enable |
| zone_schedule_status | Zone Schedule Active Zone |
| zone_schedule_day | Zone Schedule Day |
| zone_schedule_start_hour | Zone Schedule Start Hour |
| zone_schedule_start_minute_halfhour | Zone Schedule Start Minute |
| zone_schedule_end_hour | Zone Schedule End Hour |
| zone_schedule_end_minute_halfhour | Zone Schedule End Minute |
| zone_schedule_interval_mode | Zone Schedule Interval Mode |
| zone_schedule_copy_days_mask | Zone Schedule Copy Days |
| boost_mode | Boost Mode |
| boost1_supply_fan_speed | Boost 1 Supply Fan Speed |
| boost1_extract_fan_speed | Boost 1 Extract Fan Speed |
| boost1_duration_minutes | Boost 1 Duration |
| boost2_supply_fan_speed | Boost 2 Supply Fan Speed |
| boost2_extract_fan_speed | Boost 2 Extract Fan Speed |
| boost2_duration_minutes | Boost 2 Duration |
| ghe_mode | Ground Heat Exchanger Mode |
| ghe_summer_activation_temperature | GHE Summer Activation Temperature |
| ghe_winter_activation_temperature | GHE Winter Activation Temperature |
| ghe_max_opening_time_hours | GHE Maximum Opening Time |
| ghe_regeneration_time_hours | GHE Regeneration Time |
| ghe_manual_regeneration_start | GHE Manual Regeneration Start |
| alarm_panel_enable | Alarm Input Enable |
| alarm_panel_logic | Alarm Input Logic |
| alarm_panel_operation_mode | Alarm Panel Operation Mode |
| supply_fan_control_during_alarm_signal | Supply Fan Control During Alarm |
| extract_fan_control_during_alarm_signal | Extract Fan Control During Alarm |
| alarm_panel_ventilation_function | Alarm Ventilation Function Enable |
| supply_fan_control_ventilation_mode | Supply Fan Control (Ventilation Function) |
| extract_fan_control_ventilation_mode | Extract Fan Control (Ventilation Function) |
| ventilation_duration_minutes | Ventilation Duration |
| ventilation_interval_hours | Ventilation Interval |
| secondary_heater_allowed_in_ventilation_mode | Secondary Heater Allowed in Ventilation |
| exchanger_cleaning_start_hour | Heat Exchanger Cleaning Start Hour |
| start_filter_replacement_procedure | Start Filter Replacement Procedure |
| supply_filter_class | Supply Filter Class |
| extract_filter_class | Extract Filter Class |
| filters_status_and_command | Filter Service Status / Command |
| filter_time_reset_target | Filter Runtime Reset Target |
| additional_equipment_enable_mask | Additional Equipment Enable Mask |
| unit_current_status | Unit Current Status |
| comfort_temperature_current | Comfort Temperature (Current) |
| outdoor_temperature | Outdoor Air Temperature |
| leading_temperature | Leading Air Temperature *(pending physical confirmation)* |
| lead_temperature_sensor_type | Leading Temperature Sensor Type |
| regulation_mode | Temperature Regulation Mode |
| intake_temperature | Outdoor Air Temperature *(alternate source)* |
| extract_temperature | Extract Air Temperature |
| supply_temperature | Supply Air Temperature |
| exhaust_temperature | Exhaust Air Temperature |
| secondary_sensor_temperature | Secondary Sensor Temperature |
| scp_temperature | Control Panel Temperature |
| panel_temperature | Control Panel Temperature |
| temperature_behind_preheater | Preheater Downstream Air Temperature |
| temperature_behind_secondary_heater | Secondary Heater Downstream Air Temperature |
| ghe_status | Ground Heat Exchanger Status |
| ghe_temperature | Ground Heat Exchanger Temperature |
| ghe_regeneration_status | Ground Heat Exchanger Regeneration Status |
| cooler_status | Cooler Status |
| cooler_current_control | Cooler Current Control |
| cooler_blockade_time_remaining | Cooler Block Time Remaining |
| days_of_operation | Operating Days |
| days_to_inspection | Days Until Service |
| days_until_device_lock | Days Until Lockout |
| filter_detection_type | Filter Detection Method |
| supply_filter_replacement_needed | Supply Filter Replacement Required |
| supply_filter_signal_source | Supply Filter Signal Source |
| extract_filter_detection_type | Extract Filter Detection Method |
| extract_filter_replacement_needed | Extract Filter Replacement Required |
| extract_filter_signal_source | Extract Filter Signal Source |
| supply_filter_dirt_level | Supply Filter Condition |
| supply_filter_working_days | Supply Filter Operating Days |
| extract_filter_dirt_level | Extract Filter Condition |
| extract_filter_working_days | Extract Filter Operating Days |
| aggregate_current_control | Aggregate Current Control |
| chiller_alarm | Chiller Alarm |
| unit_defrosting_status | Unit Defrost Status |
| secondary_heater_type | Secondary Heater Type |
| secondary_heater_status | Secondary Heater Status |
| secondary_heater_current_control | Secondary Heater Current Control |
| secondary_heater_overtemperature | Secondary Heater Overtemperature Alarm |
| preheater_type | Preheater Type |
| preheater_status | Preheater Status |
| preheater_current_control | Preheater Current Control |
| preheater_overtemperature | Preheater Overtemperature Alarm |
| control_mode | Fan Control Mode |
| supply_fan_operation | Supply Fan Status |
| supply_fan_current_control | Supply Fan Current Control |
| extract_fan_operation | Extract Fan Status |
| extract_fan_current_control | Extract Fan Current Control |
| bypass_current_control | Bypass Current Control |
| aggregate_state | Aggregate State |
| bypass_state | Bypass State |

## 4.2 Alarm title normalization pattern

For `alarm_bitmaps` names in the register map, prefer this format:

- `<Subsystem> <Condition> Alarm` for active fault conditions
- `<Subsystem> <Condition> Fault` for hardware/sensor failures
- `<Subsystem> <Maintenance/Event>` for non-fault service events

Examples:

- `communication_error_supply_pressure_flow_sensor` -> `Supply Pressure/Flow Sensor Communication Fault`
- `no_exhaust_fan_confirmation` -> `Extract Fan No-Confirmation Alarm`
- `periodic_maintenance_approaching` -> `Maintenance Due Soon`
- `unauthorized_modbus_parameter_modification` -> `Unauthorized Modbus Parameter Change`

## 5) Naming rules for integration entities

### 5.1 General rules

- Prefer **noun-first, explicit engineering context** (e.g., `Supply Air Temperature`).
- Avoid ambiguous words such as `leading`, `intake`, or `comfort` without context.
- Use `Stage` instead of `G1/G2/G3` in UI-facing names.
- Use full words in names; abbreviations are allowed in comments/docs only.

### 5.2 Units and device classes

- Temperature: `°C`, device class `temperature`
- Humidity: `%`, device class `humidity`
- CO2: `ppm`, device class `carbon_dioxide`
- Duration: `min`, `d`, device class `duration`

### 5.3 Recommended status naming

- Binary status points should end with `Status` or `Required`.
- Fault/alarm points should include `Fault` or `Alarm`.

Examples:

- `Supply Fan Fault`
- `Extract Fan Fault`
- `Secondary Heater Overtemperature Alarm`

## 6) Control semantics (for later normalization)

- `Setpoint`: target value configured by user/automation.
- `Current`: measured or current runtime value.
- `Enable`: command/permission style boolean.
- `Status`: runtime state feedback.

Avoid mixing these in one label.

## 7) Implementation guidance for this repo

When applying normalization later:

1. Keep a stable internal identifier (address + slug) unchanged.
2. Rename only user-facing labels and translation strings.
3. Preserve backwards compatibility in automations by not changing service field keys unless migration is provided.
4. Apply canonical names consistently across sensors, numbers, switches, and options-flow fields.
5. Treat canonical names in `docs/plum_modbus_register_map.yaml` as an English baseline; provide non-English labels via Home Assistant translations.

## 8) Notes and caveats

- Some vendor terms may reflect product-specific airflow topology.
- If a physical point cannot be proven equivalent to canonical terminology, keep vendor term but append context.

Example:

- `Leading Air Temperature (Vendor)` until confirmed as `Supply Air Temperature`.
