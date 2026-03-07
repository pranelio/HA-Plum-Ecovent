# Hardware Connection Guide

This guide helps you connect supported ventilation units to Home Assistant through this integration.

Most units in this ecosystem expose Modbus on **RS485/RTU**, not native local Modbus TCP.
In practice, users are expected to provide a **Modbus RTU-to-TCP adapter (gateway)** and wire RS485 accordingly.

The structure is vendor-first, and can be expanded with model-specific pages later.

## Vendor guides

- Ensy: [docs/hardware_connection/ensy.md](hardware_connection/ensy.md)
- OXYGEN: [docs/hardware_connection/oxygen.md](hardware_connection/oxygen.md)
- Rotenso: [docs/hardware_connection/rotenso.md](hardware_connection/rotenso.md)
- ProAir: [docs/hardware_connection/proair.md](hardware_connection/proair.md)

## General requirements

- Modbus RTU-to-TCP adapter (gateway), correctly powered and commissioned
- RS485 wiring from unit bus to gateway (`A/B` and reference/ground where required)
- Matching serial parameters between unit and gateway (baud, parity, stop bits, slave ID)
- Network reachability from Home Assistant host to gateway IP/port
- Modbus TCP port access (commonly `502`, gateway/config dependent)
- Correct Modbus Unit/Slave ID (commonly `1`, vendor/model dependent)

## Recommended workflow

1. Confirm physical commissioning of the ventilation unit and RS485 bus.
2. Install and wire the RTU-to-TCP gateway to the unit RS485 interface.
3. Configure gateway serial settings to match the unit bus settings.
4. Confirm network/IP assignment of the gateway.
5. Test TCP connectivity from Home Assistant host to gateway IP/port.
6. Add the integration, choose `Modbus TCP`, and configure host/port/unit.
7. Verify live sensors first, then controls.
8. Adjust `update_rate` and optional entities in options flow after setup.

## Notes

- Vendor app/cloud connectivity does not guarantee local Modbus TCP availability.
- For this integration path, treat RTU-to-TCP gateway usage as the default/expected setup.
- Exact wiring/commissioning details can vary by installer profile and firmware.
- `Modbus RTU` appears in setup flow for roadmap visibility, but is not yet available in this release.
