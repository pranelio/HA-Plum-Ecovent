# Release Checklist

This checklist keeps changelog, code versioning, and Git tags aligned.

## 1) Prepare release notes
- Update `CHANGELOG.md`:
  - Create/update release section `## [x.y.z] - YYYY-MM-DD` (or pre-release like `x.y.z-bN`).
  - Ensure release notes include any user-visible behavior changes and setup-flow changes.

## 1.1) Verify documentation alignment
- Confirm user-facing docs reflect current setup behavior:
  - `README.md`
  - `docs/hardware_connection_guide.md`
  - `docs/supported_tested_devices.md`
- Confirm developer references reflect architecture/source-of-truth direction:
  - `docs/dev/README.md`
  - `docs/plum_modbus_register_map.yaml`

## 2) Align version fields
- Update `custom_components/plum_ecovent/manifest.json`:
  - `"version": "x.y.z"` (or `x.y.z-bN` for pre-release)
- Update `custom_components/plum_ecovent/const.py`:
  - `__version__ = "x.y.z"` (or matching `x.y.z-bN`)
- Ensure both values are identical.

## 3) Validate locally
- Run tests:
  - `pytest -q`
- Optional (recommended when available):
  - `ruff check .`
  - `mypy custom_components/plum_ecovent`

## 4) Commit and tag
- Commit with a release message:
  - `git commit -am "release: x.y.z"`
- Create annotated tag:
  - `git tag -a x.y.z -m "x.y.z"`
  - For pre-release: `git tag -a x.y.z-bN -m "x.y.z-bN"`

## 5) Publish
- Push branch:
  - `git push`
- Push tag:
  - `git push origin <tag>`

## 6) Verify release state
- Confirm tag exists locally:
  - `git tag --list`
- Confirm `CHANGELOG.md`, `manifest.json`, and `const.py` all reference the same version.
