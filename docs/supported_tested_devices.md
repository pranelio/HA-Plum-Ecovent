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
| Easy C150 | Likely support, not tested |  |
| Easy C150E | Likely support, not tested | Enthalpy variant of Easy C series. |
| Easy C200 | Likely support, not tested |  |
| Easy C200E | Likely support, not tested | Enthalpy variant of Easy C series. |
| Easy C250 | Likely support, not tested |  |
| Easy C250E | Likely support, not tested | Enthalpy variant of Easy C series. |
| Easy V200 | Likely support, not tested |  |
| Easy V200E | Likely support, not tested | Enthalpy variant of Easy V series. |
| Easy V400 | Likely support, not tested |  |
| Easy V400E | Likely support, not tested | Enthalpy variant of Easy V series. |
| Easy V500 | Likely support, not tested |  |
| Easy V500E | Likely support, not tested | Enthalpy variant of Easy V series. |
| Easy V600 | Likely support, not tested |  |

## Vendor: Rotenso

Residential lineup is **highly likely supported** due to known/shared Plum ecoVENT backbone,
but exact public model list is still pending confirmation.

| Model | Status | Notes |
|---|---|---|
| Rotenso residential HRV/ERV lineup (models TBD) | Likely support, not tested |  |

## Vendor: ProAir

Residential lineup is **highly likely supported** due to known/shared Plum ecoVENT backbone,
but complete public model list is still pending confirmation.

| Model | Status | Notes |
|---|---|---|
| ProAir PA700LI | Likely support, not tested |  |


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
