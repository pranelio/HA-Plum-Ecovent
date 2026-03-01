# Plum Ecovent

Home Assistant integration for Plum Ecovent ventilation units using Modbus (TCP or RTU).

Installation
- Copy the `plum_ecovent` folder into your `custom_components` folder, so the path becomes `custom_components/plum_ecovent`.
- Restart Home Assistant.

Configuration
- Configure using the UI via Integrations → Add Integration → Plum Ecovent.
- Choose the Modbus interface type: `TCP` (host + port) or `RTU` (serial port + baudrate).

Platforms

The integration creates a **device** that represents your Ecovent controller.
Four platforms are available by default, each reading or writing a dedicated
Modbus register.  You can tweak the addresses in `const.py` if necessary.

* **Sensor** – read a numeric register value
* **Binary sensor** – read a boolean register
* **Switch** – toggle a register between `0`/`1`
* **Number** – treat a register as a writable numeric value


Developer notes
- This integration uses `pymodbus` for Modbus communication. The dependency is declared in `manifest.json`.
- The integration provides a small `ModbusClientManager` wrapper in `modbus_client.py` to manage connections.

Blueprint alignment
- Scaffolding follows the ludeeus `integration_blueprint` layout: `manifest.json`, `config_flow.py`, translations, and `hacs.json`.

Contributing
- See the repository README for contribution guidelines.
