# Plum Ecovent (Home Assistant custom integration)

Control and monitor Plum Ecovent ventilation units via **Modbus TCP**. The integration exposes controller registers as standard Home Assistant entities (sensors, binary sensors, switches, numbers) with device registry support, configurable polling interval, and HACS-friendly packaging.

## Features
- Modbus TCP client with robust signature fallbacks and connection-safe shutdown
- Auto-created device and entities for key registers (temps, fans, filters, modes, setpoints)
- Configurable polling interval (`update_rate`) and unit id
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
2) Enter:
   - Host/IP of the Ecovent Modbus TCP server
   - Port (default `502`)
   - Unit ID (default `1`)
   - Update rate in seconds (default `30`)
3) A device is created with entities for sensors, binary sensors, switches, and numbers from `registers.py`.

### Options / Tuning
- `update_rate`: coordinator polling interval (seconds). Set higher to reduce bus load; lower for faster updates.  
- Edit `custom_components/plum_ecovent/registers.py` to add/remove registers or adjust metadata (units, categories, skip intervals, filters).

## Usage
- Entities expose live values (e.g., CO2, temperatures, fan speeds) and controls (boost/auto, heater bits, numeric setpoints).  
- Automations can react to entity state or call services to write registers via the switch/number entities.  
- Availability reflects Modbus read/write health; connection issues log warnings.

## Requirements
- Home Assistant Core / OS / Supervised with network access to the Ecovent.  
- `pymodbus` is pulled automatically; ensure outbound TCP to the device port.

## Troubleshooting
- Duplicate unique_id warnings: reload the integration after updates so new IDs are applied.  
- Connection errors: verify IP/port, unit ID, and firewall; increase `update_rate` if the bus is saturated.  
- Signature/type errors: integration already falls back across pymodbus signatures; update to latest release if you still see them.
- Unique ID migration (post-update): if entities remain ignored due to old IDs, remove the Plum Ecovent integration and re-add it, or delete the affected entries from **Settings → Devices & Services → Entities** (show disabled/hidden), then reload. The integration now appends an index to unique IDs to avoid collisions.

## Contributing
PRs are welcome. Please include test results (`pytest -q`) and note any register additions or breaking changes.

## Release Process
Use the release checklist in `RELEASE.md` for every release.

Quick flow:
1) Update version in:
   - `custom_components/plum_ecovent/manifest.json` (`version`)
   - `custom_components/plum_ecovent/const.py` (`__version__`)
2) Move release notes from `## [Unreleased]` into a new version section in `CHANGELOG.md`.
3) Run validation:
   - `pytest -q`
4) Commit and tag with the same version string (example: `0.3.0-b1`).
5) Push branch and tag:
   - `git push`
   - `git push origin 0.3.0-b1`