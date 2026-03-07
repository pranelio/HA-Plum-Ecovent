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

## Home Assistant quality scale roadmap (self-assessed)

Current estimate: **Bronze reached (self-assessed)**.

### Bronze milestone (reached)
- [x] Add `custom_components/plum_ecovent/quality_scale.yaml` and track each rule + exemptions.
- [x] Migrate runtime storage from `hass.data[DOMAIN][entry_id]` to `ConfigEntry.runtime_data`.
- [x] Set `has_entity_name = True` consistently for all entity platforms.
- [x] Ensure config-flow field help text uses `data_description` style context where applicable.
- [x] Keep config-flow coverage comprehensive for all happy/failure paths and uniqueness checks.

### Silver milestone (not reached)
- [ ] Increase measured overall integration coverage to >95% and keep it enforced in CI.
- [ ] Define `PARALLEL_UPDATES` per platform to control concurrent updates.
- [x] Improve availability logging to log once on disconnect and once on recovery (avoid log spam).
- [ ] Verify/document reauth rule exemption (no authentication flow for local Modbus device).
- [ ] Expand docs with explicit installation/configuration parameter reference.

### Gold milestone (not reached)
- [ ] Add entity translation keys for names (and icon translations where relevant).
- [ ] Add `entity_disabled_by_default` for noisy/less-used entities.
- [ ] Add reconfigure flow and repair issue guidance where user intervention is required.
- [ ] Expand end-user docs: supported functions/entities matrix, update behavior details, use-cases, automation examples.
- [ ] Evaluate device discovery feasibility (DHCP/zeroconf/manual import) and document exemptions if not technically possible.
- [ ] Create an ESPHome device blueprint/example that can expose zeroconf discovery and connection-state presence to simplify integration setup.

### Platinum milestone (not reached)
- [ ] Move toward strict typing across integration modules and tests (mypy strict target).
- [ ] Validate all dependencies and I/O paths are fully async and efficient under load.
- [ ] Benchmark and optimize polling/data handling to reduce network and CPU usage.
- [ ] Document any Platinum rule exemptions (for non-HTTP integrations, e.g., websession injection not applicable).

## Feature roadmap
### Short-term (next beta)
- [ ] Implement alarm register support (state/fault registers, severity mapping, and entity exposure).
- [ ] Implement notification support for alarms (persistent notifications/events and automation-friendly metadata).
- [ ] Add Home Assistant trigger support for alarms.
- [ ] Add calculated sensor support (e.g., efficiency and other derived metrics where data quality allows).
- [ ] Improve Modbus communication:
	- [ ] Dynamic polling strategy based on enabled entities and feature usage.
	- [ ] Batch/multi-register reads where possible to reduce call count and bus overhead.
- [ ] Implement remaining registers from the manufacturer list.

### Later
- [ ] Improve Modbus communication:
	- [ ] Implement RTU transport behind the existing config-flow connection type option, then extend with automatic connection parameter detection where feasible.
- [ ] Add `climate` entity support for temperature control where the device exposes writable setpoint/control registers.
- [ ] Add `fan` entity support for fan levels/speeds where supported by the device model.
- [ ] Add additional platforms (`select`, `text`, `button`, etc.) where they map cleanly to device capabilities.
- [ ] Add ESPHome device support with fallback behavior for lost communication with Home Assistant.
- [ ] Provide an ESPHome configuration mechanism/template to generate usable baseline configs, including fallback settings.

### Recently completed
- [x] Refactor config flow for protocol-first setup:
	- [x] Ask for connection type first (`Modbus TCP` / `Modbus RTU`).
	- [x] Keep `Modbus RTU` visible but disabled (not implemented yet).
	- [x] For `Modbus TCP`, require only host, port, and unit address.
	- [x] Move `update_rate` out of config flow (options flow only).
	- [x] Do not request device name in config flow (use Home Assistant naming conventions).
- [x] Add feature discovery by reading optional registers and adapting entities.
- [x] Add feature enable/disable controls in the options flow after setup.
- [x] Constrain options-flow override lists to interactable entities only (responding/discovered), with split force-enable/force-disable choices and empty-list user feedback.
- [x] Expand register discovery classification and retries:
	- [x] Build `available`, `non_responding`, and `unsupported` register lists during probe.
	- [x] Classify Modbus exception responses (illegal function/address/value/refused) as `unsupported`.
	- [x] Retry only `non_responding` registers with bounded timeout/retry policy (max 3 attempts).
	- [x] Create entities only from `available` registers; avoid noisy unavailable entities for other classes.
- [x] Fix entity naming/ID composition to avoid duplicated domain prefix patterns like `sensor.plum_ecovent_plum_ecovent_comfort_temperature`.
- [x] Expand documentation with clearer hardware and software setup instructions (wiring, bus setup, HA config, troubleshooting).

## Completed
- [x] Introduce a `DataUpdateCoordinator` to centralize polling and connection management.
- [x] Add an options flow to tweak update interval and unit ID after setup.
- [x] Enhance `ModbusClientManager` with retries/backoff and timeout config; surface connection state in entity availability/logs.
- [x] Validate reachability during config flow (connection test).
- [x] Provide a migration/cleanup guide for updated `unique_id` formats.
- [x] Add options flow control to adjust `update_rate` post-setup.
- [x] Maintain a `__version__` constant, release tags, and changelog.
- [x] Use `custom_components/plum_ecovent/plum_modbus_register_map.yaml` as canonical runtime source and remove duplicate register-map markdown source.
- [x] Align runtime entity names in YAML with HVAC naming conventions and fix Extract/Exhaust label mapping.
- [x] Add regression tests/docs for canonical English naming baseline with translation-aware guidance.

See `README.md` for usage notes.