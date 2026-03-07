# Development Resources

Developer-only reference material for this integration.

## Protocol and register references
- [plum_modbus_protocol_spec.md](../plum_modbus_protocol_spec.md)
- [plum_modbus_register_map.yaml](../../custom_components/plum_ecovent/plum_modbus_register_map.yaml)

`plum_modbus_register_map.yaml` is the canonical register source used by the integration runtime loader (`custom_components/plum_ecovent/registers.py`).
`integration.entities` should reference canonical entries by `register` (name key from top-level `registers`) and keep only HA-specific metadata.

### Naming and translations
- Canonical names in `integration.entities` are the English baseline used for runtime metadata consistency and tests.
- Localized display text for other languages should be implemented through Home Assistant translations, not by changing register keys or runtime structure.
- Keep `register` and `key` stable when adding translations.

## Internal design conventions
- [hvac_naming_conventions.md](../hvac_naming_conventions.md)
- [../../AGENTS.md](../../AGENTS.md)

These files are not required for end users installing or operating the integration.
