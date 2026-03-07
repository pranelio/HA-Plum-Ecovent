# TODO

Current backlog for the integration.


## Next up (quality/tooling)
- [ ] Add a GitHub Actions workflow for `pytest`, `ruff`, and `mypy`.
- [ ] Improve typing coverage (PEP 484) and fix mypy/ruff findings.
- [ ] Add `tox`/`nox` config for multi-version local test runs.
- [ ] Add more granular unit tests per platform (`sensor`, `binary_sensor`, `switch`, `number`) and consider hardware-in-the-loop tests.
- [ ] Extend docs with more automation examples and screenshots.
- [ ] Provide a small CLI utility to read/write registers outside Home Assistant.
- [ ] Remove remaining `hass.data[DOMAIN][entry_id]` runtime fallbacks and use `ConfigEntry.runtime_data` consistently.
- [ ] Re-audit `quality_scale.yaml` statuses against actual implementation/tests and correct any optimistic "done" markers.

## Feature roadmap
### Short-term (next beta)
- [ ] Add Home Assistant trigger/event support for alarm transitions.
- [ ] Expand alarm coverage using register alarm tables (state/fault/severity mapping beyond current notification-marked entities).
- [ ] Add calculated sensor support (e.g., efficiency and other derived metrics where data quality allows).
- [ ] Improve Modbus communication:
	- [ ] Dynamic polling strategy based on enabled entities and feature usage.
	- [ ] Batch/multi-register reads where possible to reduce call count and bus overhead.
- [ ] Implement remaining registers from the manufacturer list.

### Later
- [ ] Improve Modbus communication:
	- [ ] Implement RTU transport behind the existing config-flow connection type option, then extend with automatic connection parameter detection where feasible.
- [ ] Add additional platforms (`select`, `text`, `button`, etc.) where they map cleanly to device capabilities.
- [ ] Add ESPHome device support with fallback behavior for lost communication with Home Assistant.
- [ ] Provide an ESPHome configuration mechanism/template to generate usable baseline configs, including fallback settings.

### Recently completed (b4)
- [x] Added climate entity support with dynamic capability-safe control exposure.
- [x] Added climate auto-power-on safety before enabling `AUTO` mode or `Boost` while unit is off.
- [x] Removed standalone auto/boost switch entities now superseded by climate controls.
- [x] Added notify platform support for alarm notifications with transition-based persistent notifications.
- [x] Added explicit YAML notification routing (`notification: true`) and excluded notification-routed items from device-page entities.
- [x] Simplified user README and added beta disclaimer.

See `README.md` for usage notes.