# Plum Ecovent (Home Assistant Integration)

Home Assistant custom integration for Plum ecoVENT over Modbus TCP.

It creates sensors, binary sensors, switches, and numbers for supported registers and keeps them updated with a coordinator.

## Installation

### HACS (recommended)
1. Open HACS → **Integrations** → **Custom repositories**.
2. Add this repository as type **Integration**.
3. Install **Plum Ecovent**.
4. Restart Home Assistant.

### Manual
1. Copy `custom_components/plum_ecovent` to `/config/custom_components/plum_ecovent`.
2. Restart Home Assistant.

## Setup
1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Plum Ecovent**.
3. Enter:
   - **Host** (IP/DNS)
   - **Port** (default `502`)
   - **Unit ID** (default `1`)
   - **Update rate** in seconds (default `30`)
4. Finish setup.

The integration reads static device metadata (firmware, serial, model) during setup and stores it in Home Assistant device info.

## Usage
- Use created entities in dashboards and automations.
- Use switch/number entities to control fan modes and setpoints.
- Adjust options later from the integration page (for example `update_rate`, unit settings, optional entities).

## Notes
- Requires network reachability from Home Assistant to the ecoVENT Modbus TCP endpoint.
- Connection or read/write issues are surfaced in entity availability and logs.