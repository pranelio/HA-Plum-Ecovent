# Release Checklist

This checklist keeps changelog, code versioning, and Git tags aligned.

## 1) Prepare release notes
- Update `CHANGELOG.md`:
  - Keep upcoming work under `## [Unreleased]`.
  - Create a new release section `## [x.y.z] - YYYY-MM-DD`.
  - Move completed items from `Unreleased` into the new section.

## 2) Align version fields
- Update `custom_components/plum_ecovent/manifest.json`:
  - `"version": "x.y.z"`
- Update `custom_components/plum_ecovent/const.py`:
  - `__version__ = "x.y.z"`
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

## 5) Publish
- Push branch:
  - `git push`
- Push tag:
  - `git push origin x.y.z`

## 6) Verify release state
- Confirm tag exists locally:
  - `git tag --list`
- Confirm `CHANGELOG.md`, `manifest.json`, and `const.py` all reference the same version.
