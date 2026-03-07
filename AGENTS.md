# AGENTS.md

Agent operating guide for `HA-Plum-Ecovent`.

This file defines how coding agents should plan, implement, and verify changes in this repository.
The goal is predictable, high-quality, low-risk contributions with clean architecture and clear tests.

## 1) Core principles

- **Safety first**: never make changes that could silently alter HVAC behavior without explicit user intent.
- **Small, reversible changes**: prefer narrow PR-sized edits over broad rewrites.
- **Root-cause fixes**: avoid superficial patches; fix the source of defects.
- **No hidden behavior**: configuration and defaults must be explicit, documented, and testable.
- **Consistency over cleverness**: follow existing structure and Home Assistant integration patterns.

## 2) Scope and change discipline

- Only change files required for the task.
- Do not rename public entities/options/services unless requested.
- Avoid introducing new dependencies unless justified by strong technical need.
- Keep backward compatibility unless a breaking change is explicitly approved.
- If a requirement is ambiguous, choose the simplest behavior and document assumptions.

## 3) Architecture expectations

### 3.1 Integration boundaries

- Domain: `plum_ecovent`.
- Runtime state belongs in `ConfigEntry.runtime_data` (not ad-hoc global storage).
- Use `DataUpdateCoordinator` for polling, connectivity transitions, and coordinated refresh.
- Platform modules (`sensor`, `binary_sensor`, `switch`, `number`, `climate`, `notify`) should be thin adapters over shared models/coordinator data.

### 3.2 Modbus responsibilities

- Keep transport/client logic in `modbus_client.py`.
- Keep register catalog and metadata in `registers.py`.
- Keep entity construction logic deterministic from register metadata + discovered capabilities.
- Keep feature exposure capability-aware and safe:
  - only expose climate/notify controls supported by discovered available registers,
  - hide unsupported controls instead of exposing broken entities/actions.
- Treat Modbus exception responses distinctly from transport failures:
  - transport timeout/no response => non-responding path
  - explicit Modbus exception (e.g., illegal function/address/value) => unsupported path

### 3.4 Notification routing

- Notification routing must be explicit in `integration.entities` metadata (`notification: true`).
- Do not infer notification routing from `device_class` or naming heuristics.
- Entities routed to notify should not be created as normal device-page entities.

### 3.3 Config flow and options flow

- Config flow should collect only setup-critical connection parameters.
- Runtime tuning and optional behavior belong in options flow.
- Validate reachability in config flow with bounded timeout/retry behavior.
- User-facing error messages must be specific and actionable.

## 4) Code quality standards

- Add type hints for new/changed Python code.
- Keep functions cohesive and short; avoid large multi-purpose blocks.
- Prefer explicit names over abbreviations.
- Use structured, concise logging (include context keys like host/unit/register when useful).
- Prevent log spam: log transitions (disconnect/recover), not every poll failure.
- Avoid inline comments unless they explain non-obvious intent or protocol nuance.

## 5) Error handling and resilience

- Never allow uncontrolled startup/poll hangs; all I/O must be bounded by timeout.
- Use retry with clear attempt limits and deterministic stop conditions.
- Degrade gracefully:
  - partial register availability should still allow integration setup where safe
  - unavailable/unsupported features should not create noisy broken entities
- Preserve Home Assistant responsiveness; avoid blocking operations in critical paths.

## 6) Testing standards

- Any behavior change should include or update tests in `tests/`.
- Prefer focused unit tests first, then broader integration-like tests if needed.
- At minimum, cover:
  - happy path
  - expected failure path(s)
  - edge condition introduced by the change
- Keep tests deterministic (no real network/hardware dependencies in default test suite).

## 7) Documentation standards

When behavior, configuration, or capabilities change, documentation updates are **required in the same change set**:

- `README.md` for user-facing setup/usage changes.
- `CHANGELOG.md` for release-visible changes.
- `docs/*` for protocol/device/connection specifics when relevant.
- Keep wording concrete (what changed, why, impact, migration if any).
- Do not defer documentation to a follow-up PR for shipped behavior changes.

## 8) Versioning and release hygiene

- Keep `custom_components/plum_ecovent/manifest.json` version in sync with `custom_components/plum_ecovent/const.py` (`__version__`).
- Do not tag releases automatically unless explicitly requested.
- Prefer project’s established pre-release style (`x.y.z-bN`) unless maintainers define a new convention.

## 9) Agent workflow checklist (required)

Before coding:
- Confirm task scope and affected files.
- Identify existing tests and architecture touchpoints.

During coding:
- Implement minimal, coherent patch set.
- Keep APIs and entity IDs stable unless change is intentional.

After coding:
- Run relevant tests.
- Re-check for lint/type issues in changed files.
- Verify docs/version updates are complete before marking done.
- Summarize assumptions, risks, and follow-up items.

## 10) Definition of done

A change is complete when:

- Implementation matches requested behavior.
- Tests for changed behavior pass locally.
- No unrelated refactors or churn were introduced.
- Documentation and version metadata are updated when needed.
- Operational risk (timeouts/retries/logging) is explicitly addressed.

---

## Repository quick map

- Integration code: `custom_components/plum_ecovent/`
- Tests: `tests/`
- User docs: `README.md`
- Deep docs/specs: `docs/`
- Work planning: `TODO.md` and local-only working notes
