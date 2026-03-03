# Ensy Hardware Connection

## Scope

Vendor-level guidance for Ensy units known or expected to expose the same Plum ecoVENT backbone.

## Known tested example

- Wave AHU-400

## Likely default RS-485 / Modbus profile

- Serial settings are likely `9600` baud, `no parity`, `1` stop bit, address `1`.
- Wire `RS-485 A` to `DC+` and `RS-485 B` to `DC-` on the unit.
- Connect unit ground to the RTU-to-TCP adapter ground.
- Use `120 Ω` termination at both ends of the RS-485 line.
- Modbus serial settings are usually not user-exposed; changing them typically requires installer/service access.

## Connection checklist

- Confirm RTU-to-TCP adapter is installed and reachable on the network
- Confirm adapter serial settings match the unit bus profile
- Confirm target TCP IP/port and Unit/Slave ID

## Home Assistant setup hints

- Start with default `port=502`, `unit=1`
- Use a conservative `update_rate` first (e.g. `30` seconds)
- Validate sensors before enabling write-heavy automations

## Model-specific pages (future)

Add model pages here as coverage grows, e.g.:

- `ensy_wave_ahu_400.md`
