# DECISIONS

This file is the canonical index for current design decisions and active project assumptions.

## Accepted decisions

### 2026-04-09: Shorthand code metadata uses a canonical `coding[]` array

Status: accepted

Implemented in the Linear project `candice report tool` under `PER-143`.

Summary:
- Each shorthand entry stores coded concepts under a top-level `coding` array.
- Each `coding[]` item is one coded concept with `classification`, `medium`, and scalar-or-null `codes` keyed by code system.
- `medium` is always explicit and uses `PATIENT`, `LM`, `EM`, or `IHC`.
- `PATIENT` is used for patient-level diagnosis or attribute concepts.
- Multiple codes for one shorthand are represented as multiple `coding[]` items, not list values inside one code-system key.

Why this shape was chosen:
- The product’s shorthand is optimized for typing speed, so one shorthand can legitimately map to more than one coded concept.
- Export logic for native and transplant outputs needs to loop over coded concepts, not reverse-engineer meaning from flattened legacy fields.
- Keeping each code-system value scalar inside one coding group means downstream code can rely on `codes["kbc"]` or `codes["transplant"]` being a single value when present.
- Allowing explicit `null` values for a code-system slot preserves “considered but not provided” without introducing list parsing or ambiguous omission semantics.
- Explicit `medium` removes ambiguity from older `null` pattern metadata and makes light microscopy (`LM`) the concrete default for generic “Pattern of injury”.
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

### Unresolved transplant-only placeholders without classification/medium

Status: pending review

Current situation:
- Some shorthand entries still only carry a legacy transplant placeholder such as `{"transplant": "VALUE"}`.
- Those entries do not yet have enough information to create a canonical `coding[]` item because the schema requires both `classification` and `medium`.

Current implementation rule:
- If an entry already has a canonical `coding[]` item and also had a legacy transplant placeholder, the placeholder should be merged into canonical schema as `transplant: null`.
- If an entry has only a transplant placeholder and no known classification/medium yet, it remains temporarily on the legacy shim until curated classification data exists.

Why this is pending:
- Forcing these entries into `coding[]` today would require inventing `classification` and `medium`, which would introduce bad data into later export logic.
