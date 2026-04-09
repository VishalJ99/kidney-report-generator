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
