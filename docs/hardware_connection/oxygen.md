# OXYGEN Hardware Connection

## Scope

Vendor-level guidance for OXYGEN units believed to use the same Plum ecoVENT backbone.

## Current compatibility stance

- Multiple Easy-series models are listed as likely compatible in supported devices docs.
- Validate per installation/model/firmware before production automation usage.

## Likely default RS-485 / Modbus profile

- Serial settings are likely `9600` baud, `no parity`, `1` stop bit, address `1`.
- Wire `RS-485 A` to `DC+` and `RS-485 B` to `DC-` on the unit.
- Connect unit ground to the RTU-to-TCP adapter ground.
- Use `120 Ω` termination at both ends of the RS-485 line.
- Modbus serial settings are usually not user-exposed; changing them typically requires installer/service access.

## Connection checklist

- Confirm RTU-to-TCP adapter is installed and reachable on the network
- Confirm adapter serial settings match the unit bus profile
- Confirm Modbus TCP endpoint availability and IP/port
- Confirm Unit/Slave ID used by controller
- Verify that firewall/router rules allow Home Assistant host access

## Home Assistant setup hints

- Try `port=502`, `unit=1` first, then adjust if installer settings differ
- Start with read-only validation (sensor updates)
- Add control automations only after write tests succeed

## Model-specific pages (future)

Create model pages when validated (e.g. `oxygen_easy_v400.md`).
