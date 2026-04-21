# DECISIONS

This file is the canonical index for current design decisions and active project assumptions.

## Accepted decisions

### 2026-04-09: Shorthand code metadata uses a canonical `coding[]` array

Status: accepted

Implemented in the Linear project `candice report tool` under `PER-143`.

Summary:
- Each shorthand entry stores coded concepts under a top-level `coding` array.
- Each `coding[]` item is one coded concept with `classification`, `medium`, and scalar-or-null `codes` keyed by code system.
- `medium` uses `PATIENT`, `LM`, `EM`, `IHC`, or `null` when every code in the group is unresolved.
- `PATIENT` is used for patient-level diagnosis or attribute concepts.
- Multiple codes for one shorthand are represented as multiple `coding[]` items, not list values inside one code-system key.
- Any coding group that has `native1`, `native2`, or `transplant` also carries `kbc`; if the universal KBC code has not been assigned yet, it is stored as `kbc: null`.

Why this shape was chosen:
- The product’s shorthand is optimized for typing speed, so one shorthand can legitimately map to more than one coded concept.
- Export logic for native and transplant outputs needs to loop over coded concepts, not reverse-engineer meaning from flattened legacy fields.
- Keeping each code-system value scalar inside one coding group means downstream code can rely on `codes["kbc"]` or `codes["transplant"]` being a single value when present.
- Allowing explicit `null` values for a code-system slot preserves “considered but not provided” without introducing list parsing or ambiguous omission semantics.
- Requiring `kbc` alongside `native1`, `native2`, or `transplant` reflects the project rule that KBC is the universal coding system under development.
- Placeholder-only coding groups should not infer a medium; when every code value is unresolved, `medium` remains `null`.
- This structure separates text expansion concerns from code/export concerns while keeping both attached to the same shorthand entry.

Current contract:
- See [docs/coding-schema.md](/Users/dross/kidney-report-generator/docs/coding-schema.md)

Compatibility note:
- Legacy top-level `classification`, `pattern_metadata`, and `codes` fields remain temporarily readable by the backend during migration, but `coding[]` is the source of truth going forward.

### 2026-04-09: Code-family names such as `native1` and `native2` come from the source workbook

Status: accepted

Summary:
- The code-family names used in runtime JSON are inherited from the source workbook, not invented later in transplant review artifacts.
- In particular, `native2` is a tracked legacy native code family and should not be treated as unexplained noise.

Source of truth:
- [phrases_flat v4 2026_01_09.xlsx](/Users/dross/kidney-report-generator/backend/app/data/phrases_flat%20v4%202026_01_09.xlsx), `CONCLUSION` sheet, row 2

Why this matters:
- The workbook defines the naming conventions for code columns, including `native1` and `native2`.
- The converter script and runtime JSON preserve those names, so any cleanup or export refactor must treat them as source-derived legacy code families unless and until they are deliberately retired.

### 2026-04-20: V0 transplant Banff lesion export codes use explicit per-column pattern groups

Status: accepted

Implemented in the Linear project `candice report tool` under `PER-168` and `PER-145`.

Summary:
- V0 transplant export support starts with the dark-pink Banff score columns from [transplant biopsy column headers.xlsx](/Users/dross/kidney-report-generator/transplant%20biopsy%20column%20headers.xlsx), `Sheet1`, row 2.
- Each Banff shorthand maps to one or more canonical `coding[]` groups with `classification: pattern`, `medium: LM`, `kbc: null`, and a concrete `transplant` export code.
- The export-code format is `banff_lesion_<COLUMN>_<VALUE>`.
- Composite shorthand creates multiple coding groups, one per target column assignment.

Current v0 column families:
- Single-column families:
  - `c4d0` to `c4d3` -> `C4D`
  - `t0` to `t3` -> `T`
  - `ti0` to `ti3` -> `TI`
  - `cv0` to `cv3` -> `CV`
  - `v0` to `v3` -> `V`
  - `ah0` to `ah3` -> `AH`
  - `cg0` to `cg3` -> `CG`
  - `g0` to `g3` -> `G`
  - `ptc0` to `ptc3` -> `PTC`
- Composite families:
  - `ct1ci0`, `ctci1`, `ctci2`, `ctci3` -> `CT` and `CI`
  - `i0_i-ifta0` through `i3_i-ifta3` -> `I` and `IIFTA`

Why this shape was chosen:
- Transplant export needs to populate explicit spreadsheet columns, not just collect free-floating codes.
- The canonical `coding[]` schema is designed for exactly this case: one shorthand can emit multiple independently exportable coded concepts.
- Encoding the target column into the `transplant` code keeps the data dictionary self-describing enough for a v0 export path without introducing a second parallel Banff mapping layer.

### 2026-04-20: Conclusion-bearing coding groups are placeholder-complete, but native-coded groups do not carry transplant placeholders

Status: accepted

Implemented in the Linear project `candice report tool` under `PER-168`.

Summary:
- Conclusion-bearing shorthand should be code-complete enough to support capture and later export work.
- When a coded concept is not native-coded, it may carry `transplant: null` as an explicit unresolved placeholder.
- When a coded concept has `native1` or `native2`, it should not also carry a `transplant` slot in that same coding group.

Current rule:
- If a coding group has `native1` or `native2`, omit `transplant` from that group.
- If a conclusion-bearing coding group has no native slot and no transplant slot yet, add `transplant: null`.
- Keep `kbc` present wherever `native1`, `native2`, or `transplant` is present; use `kbc: null` when unresolved.
- If every code in a coding group is unresolved, keep `medium: null`.

Why this shape was chosen:
- Native and transplant outputs are different downstream workflows, so a single coding group should not imply both simultaneously when the concept is currently only known in one workflow.
- Explicit placeholder slots make missing-code work visible and machine-readable, which is useful for dictionary cleanup and for UI capture checks before export logic is finalized.

### 2026-04-21: Export logic uses the report-type toggle and canonical `coding[]`

Status: accepted

Implemented in the Linear project `candice report tool` under `PER-138`.

Summary:
- Export is driven by the frontend report-type toggle: `native` and `transplant` have different output rules.
- Export should use the same shorthand parsing and canonical `coding[]` capture path as report preview generation.
- Native export groups captured codes by classification and code family, with list-valued columns for diagnosis and pattern codes across `kbc`, `native1`, and `native2`.
- Transplant export fills patient/header fields, collects diagnosis codes into a single `Diagnosis codes` column, and maps Banff pattern codes such as `T_3` into score columns such as `T = 3`.
- The frontend export action downloads an XLSX file from `POST /api/export`.
- The detailed export contract lives in [docs/export-logic.md](/Users/dross/kidney-report-generator/docs/export-logic.md).
- If two entered shorthand tokens assign different values to the same Banff score column, export should fail with a warning rather than silently choosing a value.
- Consent is exported as the raw value entered after the `Consent` prefix, for example `PISv.8`.

Why this matters:
- Export is clinically sensitive and easy to get subtly wrong, so the semantics should be documented before implementation.
- The implementation should not invent a separate interpretation of shorthand; it should consume the same canonical `coding[]` concepts that power live code capture.

## Pending review

### Provisional classification and medium assignments for transplant-only placeholder entries

Status: pending review

Current situation:
- Some shorthand entries had only a transplant placeholder and no explicit stored `classification` or `medium`.
- To finish migration away from legacy top-level `codes`, these entries were converted into canonical `coding[]` using best-effort classification/medium assignments based on the conclusion text and Candice transplant review notes.

Current implementation rule:
- Entries treated as transplant diagnoses use `classification: diagnosis`, `medium: null` while the coding group is placeholder-only.
- Entries treated as transplant patterns use `classification: pattern`, `medium: null` while the coding group is placeholder-only.
- `subop` is currently treated as `classification: attribute`, `medium: null` while the coding group is placeholder-only.
- Unresolved transplant codes are represented canonically as `codes.transplant = null`, with `kbc: null` also present.

Current provisional assignments:
- Diagnosis/null medium:
  - `a-amr`
  - `ac-amr`
  - `bl`
  - `c-amr`
  - `p-amr`
  - `polyoma`
  - `t1a`
  - `t1a-c`
  - `t1b`
  - `t1b-c`
  - `t2-c`
  - `t2a`
  - `t2b`
  - `t3`
- Pattern/null medium:
  - `ah3`
  - `ati-micro`
  - `cv3`
  - `isch`
  - `mild-ifta`
  - `mod-ifta`
  - `mvi`
  - `sev-ifta`
- Attribute/null medium:
  - `subop`

Why this is pending:
- These assignments are sufficient to eliminate the legacy schema and unblock frontend/export work, but some transplant entries may still need clinical review before they are treated as final ontology truth.
