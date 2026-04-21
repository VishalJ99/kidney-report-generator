# Export Logic

This document defines the v1 export rules implemented by the backend export endpoint.

## Purpose

The report generator creates structured export rows from the same shorthand input used to generate the report preview.

The export path should not re-parse the final prose report. It should use the shorthand parser and the resolved `coding[]` groups attached to shorthand entries.

## Inputs

The export operation receives:

- raw shorthand text
- selected report type: `native` or `transplant`
- generated/captured case codes from completed shorthand tokens

The frontend report-type toggle decides which export logic applies.

## Patient/header fields

Patient and administrative fields are taken from explicit top-of-report shorthand lines.

Current planned mappings:

| Input line prefix | Meaning | Native export column | Transplant export column |
| --- | --- | --- | --- |
| `Name ...` | Patient name | `Name` | pending: no matching transplant column in current header file |
| `NHS ...` | NHS number | `NHS number` | `NHS Number` |
| `HN ...` | Hospital number | `Hosp number` | pending: no matching transplant column in current header file |
| `NS ...` | Path number | `Path number` | `Path no` |
| `Coder ...` | Coder | `CODER` | `Coder` |
| `Date ...` | Date of biopsy | `Date` | `Date of Bx` |
| `Consent ...` | Consent/PIS value | `CONSENT PIS v 6. (Y N U)` | `Consent` |

Decision:

- “Concept boolean” refers to consent/consent boolean.
- Consent is exported as the raw value entered after the `Consent` prefix, for example `PISv.8`.

## Code source model

Export uses canonical `coding[]` groups.

Each group has:

- `classification`: `diagnosis`, `pattern`, or `attribute`
- `medium`: `PATIENT`, `LM`, `EM`, `IHC`, or `null`
- `codes`: scalar-or-null code values by code family, for example `kbc`, `native1`, `native2`, `transplant`

One shorthand can emit multiple `coding[]` groups. This is required for composite shorthand such as combined Banff scores.

## Native export

Native export writes one row per case.

For v1, native export should use list-valued columns grouped by both classification and code family.

Planned native code columns:

- `Diagnosis KBC`
- `Diagnosis native1`
- `Diagnosis native2`
- `Pattern KBC`
- `Pattern native1`
- `Pattern native2`

Future-compatible optional columns:

- `Attribute KBC`
- `Attribute native1`
- `Attribute native2`

Rules:

- For each captured `coding[]` group with `classification = diagnosis`, append its available `kbc`, `native1`, and `native2` values to the corresponding diagnosis columns.
- For each captured `coding[]` group with `classification = pattern`, append its available `kbc`, `native1`, and `native2` values to the corresponding pattern columns.
- For each captured `coding[]` group with `classification = attribute`, append its available `kbc`, `native1`, and `native2` values to the corresponding attribute columns if those columns are implemented.
- Empty/null code values are skipped.
- Duplicate values in the same cell should be deduplicated while preserving encounter order.
- Each cell contains a list of codes for the case.

Current source file for native header reference:

- `/Users/dross/kidney-report-generator/native database.xlsx`

Important native header decision:

- The existing workbook has old one-code-per-column diagnosis fields such as `Diagnosis 1 M`, `Diagnosis 2 M`, etc.
- The new export should replace that with list-valued diagnosis/pattern columns as described above.

## Transplant export

Transplant export writes one row per case.

Current source file for transplant header reference:

- `/Users/dross/kidney-report-generator/transplant biopsy column headers.xlsx`

High-level rules:

- Patient/header fields are filled from top-of-report shorthand lines.
- Diagnosis coding groups are collected into a diagnosis list column.
- Banff lesion pattern groups are mapped into specific spreadsheet score columns.
- Non-Banff pattern handling is deferred unless a clear transplant column mapping exists.

## Transplant diagnosis codes

For each captured `coding[]` group with `classification = diagnosis`:

- collect `transplant` codes when present
- collect `kbc` codes as the universal fallback/parallel system
- skip null placeholders

Layout decision:

- The legacy `DIagnosis 1`, `Diagnosis 2`, `Diagnosis 3`, and `Diagnosis 4` columns are deprecated.
- Export should use a single `Diagnosis codes` column containing a list of diagnosis codes for the case.

## Banff score export

Banff score shorthand belongs to `classification = pattern` and usually `medium = LM`.

The transplant code value encodes:

- target export column
- value to write into that column

Code format:

```text
COLUMN_VALUE
```

Example:

```text
T_3
```

Means:

- target column: `T`
- cell value: `3`

So shorthand `t3` should export `3` into the transplant `T` column.

Composite shorthand emits multiple coding groups.

Example:

```text
ctci2
```

Should emit:

```text
CT_2
CI_2
```

and export:

| Column | Value |
| --- | --- |
| `CT` | `2` |
| `CI` | `2` |

## Banff column mapping

The code prefix maps to the transplant workbook column.

| Code prefix | Export column |
| --- | --- |
| `C4D` | `C4d` |
| `CT` | `CT` |
| `CI` | `CI` |
| `I` | `I` |
| `IIFTA` | `iIFTA` |
| `TI` | `TI` |
| `T` | `T` |
| `CV` | `CV` |
| `V` | `V` |
| `AH` | `AH` |
| `CG` | `CG` |
| `G` | `Glomerulitis` |
| `PTC` | `PTC` |

The light-pink columns are out of v1 scope unless explicitly brought in later.

## Known Banff shorthand families

Single-column families:

- `c4d0` to `c4d3` -> `C4D_0` to `C4D_3`
- `t0` to `t3` -> `T_0` to `T_3`
- `ti0` to `ti3` -> `TI_0` to `TI_3`
- `cv0` to `cv3` -> `CV_0` to `CV_3`
- `v0` to `v3` -> `V_0` to `V_3`
- `ah0` to `ah3` -> `AH_0` to `AH_3`
- `cg0` to `cg3` -> `CG_0` to `CG_3`
- `g0` to `g3` -> `G_0` to `G_3`
- `ptc0` to `ptc3` -> `PTC_0` to `PTC_3`

Composite families:

- `ct1ci0` -> `CT_1`, `CI_0`
- `ctci1` -> `CT_1`, `CI_1`
- `ctci2` -> `CT_2`, `CI_2`
- `ctci3` -> `CT_3`, `CI_3`
- `i0_i-ifta0` through `i3_i-ifta3` -> `I_<score>`, `IIFTA_<score>`

## Implementation notes

- Export should call the same parser path as `/api/generate` to avoid preview/export drift.
- Export should consume `case_codes[].coding[]`, not flattened legacy `codes`.
- Existing dictionary values that used `banff_lesion_<COLUMN>_<VALUE>` were migrated to `COLUMN_VALUE` before export implementation.
- If two shorthand tokens set the same Banff column to different values, export should fail with a clear conflict warning. This represents a typo or mistake that the user should explicitly fix before exporting.
