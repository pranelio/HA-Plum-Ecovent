# Changelog

All notable changes to this project are documented in this file.

## [0.5.0-b3] - 2026-03-07
### Changed
- Updated release metadata to `0.5.0-b3` in `manifest.json` and `const.py`.

## [0.5.0-b2] - 2026-03-07
### Changed
- Switched default polling update rate to `5` seconds (`DEFAULT_UPDATE_RATE`) for new setups and fallback runtime behavior.
- Updated entity naming behavior to avoid duplicated integration prefixes in Home Assistant entity IDs by relying on entity names with `has_entity_name = True`.

### Fixed
- Removed noisy `pymodbus.logging` parser spam (unit-id mismatch and raw frame dump lines) via a targeted logger filter while keeping normal error logs.
- Added regression coverage for initial TCP setup fields, entity naming, and pymodbus noise-filter behavior.

## [0.5.0-b1] - 2026-03-07
### Added
- Protocol-first config flow: explicit connection type selection with `Modbus TCP` support and visible-but-disabled `Modbus RTU` path.
- Register capability classification during setup probe with persisted buckets: `available_registers`, `non_responding_registers`, and `unsupported_registers`.
- Modbus-level adapter validation step that combines TCP reachability with a bounded Modbus handshake/read sanity check.

### Changed
- Initial config flow now collects only required TCP connection inputs (`host`, `port`, `unit`); update interval and tuning remain in options flow.
- Setup discovery now treats explicit available-register snapshots (including empty snapshots) as authoritative, preventing fallback probing noise.
- Runtime payload now stores register support classification details for downstream setup/diagnostics use.
- Config-flow translations updated to reflect the new multi-step protocol flow and clearer verification messaging.
- Added an explicit transport seam in `ModbusClientManager` (`tcp` active now, `rtu` reserved for future implementation).
- Register capability probing now enforces a global discovery deadline and startup timeout guard to avoid long setup hangs.
- Options flow entity selection now aligns with discovered capabilities while preserving legacy override entries.
- Entity toggle choices now keep options-managed number settings hidden, preserving the options-only settings policy.
- Register definitions are now loaded from `docs/plum_modbus_register_map.yaml` (`integration.entities`) instead of duplicated hardcoded lists in `registers.py`.
- Integration entity entries now reference canonical top-level registers by name (`register`) with inherited address/unit/range metadata, reducing duplicated YAML fields.
- Integration entity display names in YAML were aligned with `docs/hvac_naming_conventions.md` (including corrected Extract/Exhaust label mapping).
- Added internal multi-group tags and icon metadata in the canonical register map for development-oriented filtering and future tooling.

### Fixed
- Verification now reports a dedicated `unit_no_response` path when adapter TCP connectivity succeeds but no Modbus response is returned for the selected address.
- Discovery/entity setup no longer creates opportunistic entities when setup explicitly determined no available registers.
- Coordinator partial-failure warnings now include sample failed registers to improve diagnostics versus generic count-only logs.
- Removed duplicate register-map markdown source in favor of the YAML canonical source.

## [0.4.3] - 2026-03-03
### Fixed
- Fixed config-flow progress state transitions so setup no longer gets stuck and now reliably reaches successful entry creation.
- Hardened Modbus TCP communication for noisy gateways by serializing requests and validating response unit/function before accepting payloads.
- Added retry/reconnect handling for mismatched or cross-framed responses to avoid request/response desynchronization loops.

### Changed
- Options flow entity selection now shows current values from coordinator data.
- Options flow current values now render with cleaner formatting and units where available.
- Updated integration version references to `0.4.3` in `manifest.json` and `const.py`.

## [0.4.2] - 2026-03-03
### Fixed
- Setup register probing now treats Modbus illegal-data/illegal-address exception responses as unsupported immediately, instead of repeatedly retrying those registers.
- Setup probing now treats timeout/no-response registers as non-working after bounded attempts and continues quickly.
- Removed retry amplification during setup probing by disabling nested client retries for probe requests.
- Reduced probe latency by using probe-specific timeout/backoff values, so setup completes faster on slow or partially supported devices.

### Changed
- Updated integration version references to `0.4.2` in `manifest.json` and `const.py`.

## [0.4.1] - 2026-03-03
### Changed
- Updated integration version references to `0.4.1` in `manifest.json` and `const.py`.
- Improved setup UX in config flow with active progress reporting during adapter verification and register probing, so long-running steps no longer appear stalled.
- Hardened Modbus reconnect behavior to force reconnect attempts during retry loops instead of being blocked by reconnect throttling.

### Fixed
- Setup now clearly reports the current running task while validation/probing is in progress.
- Reduced transient communication instability by improving read/write retry handling and reconnect flows in `modbus_client.py`.
- Treated unload-time request cancellation (`CancelledError` / pymodbus cancellation) as expected shutdown behavior to avoid false fault traces.
- Reduced coordinator warning noise by logging partial/total read failures on state transitions and adding explicit recovery logs when communication stabilizes.

## [0.4.0] - 2026-03-03
### Added
- Added local integration brand assets under `custom_components/plum_ecovent/brand/`:
	`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`, `dark_logo.png`, `dark_logo@2x.png`.

### Changed
- Updated integration version references to `0.4.0` in `manifest.json` and `const.py`.
- Aligned integration brand metadata to `plum_ecovent` for local brand asset resolution.
- Prepared release tag target `0.4.0` on `dev` branch.
- Refactored options flow to branch by task (`connection`, `optional entities`, and new `Device Settings`).
- Added grouped `Device Settings` sections for supply fan, exhaust fan, auto control, boost, and temperature values.
- Reduced device-page clutter by moving configurable number registers to options/services management instead of per-setting number entities.
- Redesigned initial setup into staged validation and discovery: adapter settings, reachability verification, then full register probing.
- Persisted discovered responding registers in config entry data and used them as the primary runtime discovery source.
- Replaced optional-only discovery behavior with unified entity selection across all definitions, with include/disable overrides applied consistently.
- Updated options flow entity management labels and behavior to reflect scanned entities rather than optional-only entities.

### Added
- Added `plum_ecovent.set_device_setting` service for automation-friendly writes to options-managed device settings.
- Added `custom_components/plum_ecovent/services.yaml` service descriptions.

## [0.3.0-b1] - 2026-03-02
### Added
- Diagnostics support via `diagnostics.py` for safer support troubleshooting.
- Complete config/options translation keys for validation and form labels.
- Optional entity metadata and helper catalog in `registers.py` to support model-dependent entity selection.
- Discovery summary logging (per platform and overall totals) during integration setup.
- Persistent optional entity selection settings in options flow (`optional entities to enable` / `optional entities to disable`).

### Changed
- Added `iot_class: local_polling` to integration metadata.
- Improved switch write behavior to read-modify-write when toggling bitmasked registers.
- Normalized number mode handling for Home Assistant compatibility.
- Improved coordinator behavior to report full read failures explicitly.
- Config flow connection validation now returns clearer reachability errors (`invalid_host`, `connection_refused`, `connection_timeout`).
- Options flow now supports updating connection settings (`host`, `port`, `name`) in addition to polling and unit settings.
- Optional entity discovery now applies user overrides and stores the discovered entity list for runtime setup.
- Platform setup now uses saved discovered definitions only; undiscovered entities are not created.

### Fixed
- Removed duplicate sensor register definition to prevent duplicate entities.
- Aligned release metadata and version references with `0.3.0-b1`.
- Optional entities manually enabled by the user are treated the same as automatically discovered entities (no explicit forced-state labeling).

## [0.2.0]
### Added
- Added options flow to adjust `update_rate` and `unit` after setup, with entry reloads.
- Implemented DataUpdateCoordinator polling; entities pull from coordinator and expose availability.
- Added connectivity check in config flow.

### Changed
- Hardened Modbus client with signature fallbacks, retries/backoff/timeouts, and cancellation-safe shutdown.
- README refreshed for HACS install/config/usage.

### Fixed
- Unique IDs now slugged with index to avoid collisions; migration notes added to README.
