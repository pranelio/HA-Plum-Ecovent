# Plum Ecovent (Home Assistant custom integration)

> ⚠️ **Beta / Active Development**
>
> This integration is under active development. Features and behavior may change between beta releases.

Control and monitor Plum Ecovent ventilation units in Home Assistant over Modbus TCP.

## Supported devices
- Compatibility list: [docs/supported_tested_devices.md](docs/supported_tested_devices.md)

## Installation
### HACS (recommended)
1. In HACS, add this repository as a **Custom repository** of type **Integration**.
2. Install **Plum Ecovent**.
3. Restart Home Assistant.

### Manual
1. Copy `custom_components/plum_ecovent/` to `/config/custom_components/plum_ecovent/`.
2. Restart Home Assistant.

## Setup
1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Plum Ecovent**.
3. Enter:
   - Host/IP
   - Port (default `502`)
   - Unit ID (default `1`)

## Basic usage
- Use the created **Climate** entity for day-to-day control.
- Use available sensors/switches/numbers for monitoring and additional settings.
- Use the **Issues** notify entity for alarm notifications.
- Use service `plum_ecovent.set_device_setting` for automation-friendly writes when needed.

## Hardware guide
- Start here for wiring and gateway setup: [docs/hardware_connection_guide.md](docs/hardware_connection_guide.md)

## Troubleshooting
- Verify device IP/port/unit ID.
- Check gateway/wiring from the hardware guide.
- Reload the integration after major version updates.

## Disclaimer
- You are responsible for safe installation and operation.
- This project is provided as-is.

