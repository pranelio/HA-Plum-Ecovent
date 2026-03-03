# TODO

Current backlog for the integration.


## Next up (quality/tooling)
- [ ] Add a GitHub Actions workflow for `pytest`, `ruff`, and `mypy`.
- [ ] Improve typing coverage (PEP 484) and fix mypy/ruff findings.
- [ ] Add `tox`/`nox` config for multi-version local test runs.
- [ ] Add more granular unit tests per platform (`sensor`, `binary_sensor`, `switch`, `number`) and consider hardware-in-the-loop tests.
- [ ] Extend docs with more automation examples and screenshots.
- [ ] Provide a small CLI utility to read/write registers outside Home Assistant.

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
- [ ] Improve availability logging to log once on disconnect and once on recovery (avoid log spam).
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
- [ ] Implement registers for alarms.
- [ ] Implement alarm notifications.
- [x] Add feature discovery by reading optional registers and adapting entities.
- [x] Add feature enable/disable controls in the options flow after setup.
- [ ] Implement remaining registers from the manufacturer list.
- [ ] Add additional platforms (`select`, `text`, `button`, etc.) if needed.

## Completed
- [x] Introduce a `DataUpdateCoordinator` to centralize polling and connection management.
- [x] Add an options flow to tweak update interval and unit ID after setup.
- [x] Enhance `ModbusClientManager` with retries/backoff and timeout config; surface connection state in entity availability/logs.
- [x] Validate reachability during config flow (connection test).
- [x] Provide a migration/cleanup guide for updated `unique_id` formats.
- [x] Add options flow control to adjust `update_rate` post-setup.
- [x] Maintain a `__version__` constant, release tags, and changelog.

See `README.md` for usage notes.