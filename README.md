# Plum Ecovent

A custom Home Assistant integration that communicates with Plum Ecovent
ventilation units over **Modbus TCP**.  It exposes controller registers as
standard Home Assistant entities, allowing you to monitor temperatures,
fan speeds, filter status and to change configuration parameters directly
from the UI or automations.

> ✅ **Purpose:** control and observe a Plum Ecovent system via its built-in
> Modbus interface. Ideal when native support is missing from Home Assistant
> or when you want full access to the unit's registers.


## Installation
1. Clone or download this repository.
2. Copy the `plum_ecovent` directory into your Home Assistant
   `custom_components` folder (e.g. `/config/custom_components/plum_ecovent`).
3. Restart Home Assistant.
4. Navigate to **Settings → Devices & Services → Add Integration** and search
   for *Plum Ecovent*.
5. Provide the IP address and port of the Modbus TCP server on your Ecovent
   device, and the Modbus unit ID (usually `1`).

HACS users can install directly from a release or the repository URL; the
`hacs.json` metadata ensures the integration appears correctly.

> **Note:** this integration depends on the `pymodbus` Python package. Home
> Assistant will normally install it automatically, but if you see an error
> such as
> 
> ```
> Unexpected error creating Modbus client
> ModuleNotFoundError: No module named 'pymodbus.client.async'
> ```
> 
> make sure your environment has `pymodbus>=2.5` available (you can install
> it manually with `pip install pymodbus`).  The component logs a clear
> message when the async client class cannot be imported.


## Usage
The integration registers a single device representing the controller.  Four
platforms are supported by default (sensor, binary_sensor, switch, number),
and each entity corresponds to a specific Modbus register.  Entities are
created automatically from the definitions in
`custom_components/plum_ecovent/registers.py`.

You can customise which registers are read or written by editing that file,
or override values via the UI once the integration is set up.

Typical entities include:

* **Temperature sensors** (CO2, supply/exhaust, outdoor, etc.)
* **Binary diagnostics** such as filter replacement needed or heater status
* **Switches** for modes like `Auto` or `Boost`
* **Numbers** for fan speed settings, temperature setpoints, etc.

Use Home Assistant automations to trigger actions based on sensor values or
to adjust configuration periodically.


## Development
- Written in Python using the Home Assistant developer framework.
- Modbus handled by [`pymodbus`](https://pymodbus.readthedocs.io/).

If you want to modify or extend the integration, follow the instructions in
`tests` to set up a development environment and run the unit tests.

### Running tests
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q
```



## Contributing
Contributions are welcome!  Please open an issue or pull request on GitHub
and include a description of the change and any testing performed.

---

*(This README is intended for users of the integration; developer-focused
notes have been moved to the repository itself.)*