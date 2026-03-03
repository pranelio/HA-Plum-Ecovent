# ProAir Hardware Connection

## Scope

Vendor-level guidance for ProAir units expected to share Plum ecoVENT backbone.

## Known product reference

- PROAIR PA700LI (listed as likely compatible, not yet fully field-tested in this repo)

## Connection checklist

- Confirm local network access to unit/controller
- Confirm Modbus TCP endpoint settings (IP/port/unit)
- Confirm Home Assistant host can reach controller over TCP

## Home Assistant setup hints

- Start with baseline values (`port=502`, `unit=1`)
- Confirm read stability before control automations

## Model-specific pages (future)

Add validated model pages as available.
