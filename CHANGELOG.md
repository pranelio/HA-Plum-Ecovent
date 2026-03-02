# Changelog

All notable changes to this project are documented in this file.

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
