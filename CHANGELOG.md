# Changelog

## 0.2.0
- Added options flow to adjust `update_rate` and `unit` after setup, with entry reloads
- Implemented DataUpdateCoordinator polling; entities pull from coordinator and expose availability
- Hardened Modbus client with signature fallbacks, retries/backoff/timeouts, and cancellation-safe shutdown
- Added connectivity check in config flow
- Unique IDs now slugged with index to avoid collisions; migration notes added to README
- README refreshed for HACS install/config/usage
