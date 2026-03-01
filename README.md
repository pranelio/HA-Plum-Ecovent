# Plum Ecovent

Home Assistant integration for Plum Ecovent ventilation units using Modbus (TCP or RTU).

Installation
- Copy the `plum_ecovent` folder into your `custom_components` folder, so the path becomes `custom_components/plum_ecovent`.
- Restart Home Assistant.

Configuration
- Configure using the UI via Integrations → Add Integration → Plum Ecovent.
- Choose the Modbus interface type: `TCP` (host + port) or `RTU` (serial port + baudrate).

Developer notes
- This integration uses `pymodbus` for Modbus communication. The dependency is declared in `manifest.json`.
- The integration provides a small `ModbusClientManager` wrapper in `modbus_client.py` to manage connections.

Blueprint alignment
- Scaffolding follows the ludeeus `integration_blueprint` layout: `manifest.json`, `config_flow.py`, translations, and `hacs.json`.

Contributing
- See the repository README for contribution guidelines.
