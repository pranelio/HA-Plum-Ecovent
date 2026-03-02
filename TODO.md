# TODO

Current backlog for the integration.

## Required fixes (from quality audit)
- [x] Fix options flow registration so Home Assistant reliably exposes integration options (`ConfigFlow.async_get_options_flow`).
- [x] Make number writes fail-safe: only update optimistic value after successful Modbus write, and surface write failures.
- [x] Make switch command state fail-safe: do not set local on/off state when write fails; rely on coordinator refresh/result.
- [x] Harden setup compatibility for tests/stubs by safely merging config with missing `entry.options`.
- [x] Update tests to match current behavior:
	- config flow tests must mock reachability validation (`_async_test_connection`),
	- switch tests must assert bitmask-preserving register writes (not forced `1/0`).

## Next up (quality/tooling)
- [ ] Add a GitHub Actions workflow for `pytest`, `ruff`, and `mypy`.
- [ ] Improve typing coverage (PEP 484) and fix mypy/ruff findings.
- [ ] Add `tox`/`nox` config for multi-version local test runs.
- [ ] Add more granular unit tests per platform (`sensor`, `binary_sensor`, `switch`, `number`) and consider hardware-in-the-loop tests.
- [ ] Extend docs with more automation examples and screenshots.
- [ ] Provide a small CLI utility to read/write registers outside Home Assistant.

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