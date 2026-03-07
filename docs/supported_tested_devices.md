# Supported / Tested Devices

This page tracks devices that are verified with this integration.
As coverage grows, add new entries grouped by vendor.

## Vendor: Ensy

| Model | Status | Notes |
|---|---|---|
| Wave AHU-400 | Tested |  |

## Vendor: OXYGEN

| Model | Status | Notes |
|---|---|---|
| Easy C150 | Supported (untested) |  |
| Easy C150E | Supported (untested) | Enthalpy variant of Easy C series. |
| Easy C200 | Supported (untested) |  |
| Easy C200E | Supported (untested) | Enthalpy variant of Easy C series. |
| Easy C250 | Supported (untested) |  |
| Easy C250E | Supported (untested) | Enthalpy variant of Easy C series. |
| Easy V200 | Supported (untested) |  |
| Easy V200E | Supported (untested) | Enthalpy variant of Easy V series. |
| Easy V400 | Supported (untested) |  |
| Easy V400E | Supported (untested) | Enthalpy variant of Easy V series. |
| Easy V500 | Supported (untested) |  |
| Easy V500E | Supported (untested) | Enthalpy variant of Easy V series. |
| Easy V600 | Supported (untested) |  |

## Vendor: Rotenso

Residential lineup is **highly likely supported** due to known/shared Plum ecoVENT backbone,
but exact public model list is still pending confirmation.

| Model | Status | Notes |
|---|---|---|
| Rotenso residential HRV/ERV lineup (models TBD) | Highly likely supported |  |

## Vendor: ProAir

Residential lineup is **highly likely supported** due to known/shared Plum ecoVENT backbone,
but complete public model list is still pending confirmation.

| Model | Status | Notes |
|---|---|---|
| ProAir PA700LI | Supported (untested) |  |


## Contribution format

When adding a new tested device, use this structure:

- Vendor
- Model group / family
- Variant or size
- Firmware version (if known)
- What was tested (read-only sensors, controls, options flow, diagnostics)
- Any limitations or missing registers

## Status definitions

- **Tested**: Confirmed working in a real installation.
- **Supported (untested)**: Expected to work from register compatibility, but not yet field-validated.
- **Highly likely supported**: Strong evidence of shared controller/register backbone, but not yet directly validated in this repo.
- **Partial**: Core features work, with known limitations.

Tested status reflects at least basic setup + live polling verification; write-control validation may still vary by firmware and installer configuration.
