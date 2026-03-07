# Plum Ecovent (Home Assistant custom integration)

Control and monitor Plum Ecovent ventilation units via **Modbus TCP**. The integration uses a protocol-first setup flow, probes register capabilities during onboarding, and exposes supported controller registers as Home Assistant entities.

## Supported Devices
- See the live compatibility list first: [docs/supported_tested_devices.md](docs/supported_tested_devices.md)
- Includes tested units and likely-compatible families by vendor

## Features
- Protocol-first setup (`Modbus TCP` active, `Modbus RTU` visible but not yet implemented)
- Bounded Modbus validation during setup (TCP reachability + Modbus handshake)
- Register capability classification (`available`, `non_responding`, `unsupported`) for cleaner entity creation
- Configurable polling interval (`update_rate`) and unit id in options flow
- Unique IDs and entity categories for full UI management

## Installation
### HACS (recommended)
1) In HACS, choose **Custom repositories** → add this repo as **Integration**.  
2) Install **Plum Ecovent** from HACS.  
3) Restart Home Assistant.

### Manual
1) Copy `custom_components/plum_ecovent/` into `/config/custom_components/plum_ecovent/`.  
2) Restart Home Assistant.

## Configuration
1) Go to **Settings → Devices & Services → Add Integration** and search for *Plum Ecovent*.  
2) Select connection type:
   - `Modbus TCP` (supported)
   - `Modbus RTU` (currently unavailable in this release)
3) For `Modbus TCP`, enter:
   - Host/IP of the Modbus TCP endpoint (typically your RTU-to-TCP gateway)
   - Port (default `502`)
   - Unit ID (default `1`)
4) After verification and probing, a device is created with entities only for discovered supported registers.

### Options / Tuning
- `update_rate`: coordinator polling interval (seconds). Set higher to reduce bus load; lower for faster updates.
- `unit`: unit/slave ID can be tuned post-setup.
- optional entities: enable/disable discovered entities for your installation.

## Usage
- Entities expose live values (e.g., CO2, temperatures, fan speeds) and controls (boost/auto, heater bits, numeric setpoints).  
- Automations can react to entity state or call services to write registers via the switch/number entities.  
- Availability reflects Modbus read/write health; connection issues log warnings.

### Service actions
- `plum_ecovent.set_device_setting`: writes options-managed settings directly by key.

Example automation action:
```yaml
action:
   - service: plum_ecovent.set_device_setting
      data:
         setting: boost_duration
         value: 15
```

If multiple Plum entries are loaded, include `entry_id` in the service data.
Available `setting` keys are defined in `custom_components/plum_ecovent/services.yaml`.

## Requirements
- Home Assistant Core / OS / Supervised with network access to the Ecovent.  
- Modbus RTU-to-TCP adapter (gateway) for units that expose only RS485/RTU locally.
- `pymodbus` is pulled automatically; ensure outbound TCP to the device port.

## Troubleshooting
- Duplicate unique_id warnings: reload the integration after updates so new IDs are applied.  
- Connection errors: verify IP/port, unit ID, and firewall; increase `update_rate` if the bus is saturated.
- Adapter reachable but setup fails with no response: verify RS485 wiring, gateway serial parameters, and selected unit address.
- Signature/type errors: integration already falls back across pymodbus signatures; update to latest release if you still see them.
- Unique ID migration (post-update): if entities remain ignored due to old IDs, remove the Plum Ecovent integration and re-add it, or delete the affected entries from **Settings → Devices & Services → Entities** (show disabled/hidden), then reload. The integration now appends an index to unique IDs to avoid collisions.

## Removal
1) Go to **Settings → Devices & Services**.
2) Open **Plum Ecovent** and choose **Delete**.
3) Confirm removal; entities and device entries from this integration are removed.
4) Optionally delete `custom_components/plum_ecovent/` if you installed manually.

## Disclaimer
- You are responsible for safe installation, wiring, configuration, and operation of your ventilation system and any connected adapters/gateways.
- This integration is provided as-is, and the authors/maintainers accept no liability for any damage, data loss, malfunction, or other consequences resulting from installation or use.

## User Documentation
- Supported and field-tested devices: [docs/supported_tested_devices.md](docs/supported_tested_devices.md)
- Hardware connection guide: [docs/hardware_connection_guide.md](docs/hardware_connection_guide.md)
- Developer/protocol references are indexed in `docs/dev/README.md`

