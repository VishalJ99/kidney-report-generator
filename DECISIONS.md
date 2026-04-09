# DECISIONS

This file is the canonical index for current design decisions and active project assumptions.

## Accepted decisions

### 2026-04-09: Shorthand code metadata uses a canonical `coding[]` array

Status: accepted

Implemented in the Linear project `candice report tool` under `PER-143`.

Summary:
- Each shorthand entry stores coded concepts under a top-level `coding` array.
- Each `coding[]` item is one coded concept with `classification`, `medium`, and scalar `codes` keyed by code system.
- `medium` is always explicit and uses `PATIENT`, `LM`, `EM`, or `IHC`.
- `PATIENT` is used for patient-level diagnosis or attribute concepts.
- Multiple codes for one shorthand are represented as multiple `coding[]` items, not list values inside one code-system key.

Why this shape was chosen:
- The product’s shorthand is optimized for typing speed, so one shorthand can legitimately map to more than one coded concept.
- Export logic for native and transplant outputs needs to loop over coded concepts, not reverse-engineer meaning from flattened legacy fields.
- Keeping each code-system value scalar inside one coding group means downstream code can rely on `codes["kbc"]` or `codes["transplant"]` being a single value when present.
- Explicit `medium` removes ambiguity from older `null` pattern metadata and makes light microscopy (`LM`) the concrete default for generic “Pattern of injury”.
- This structure separates text expansion concerns from code/export concerns while keeping both attached to the same shorthand entry.

Current contract:
- See [docs/coding-schema.md](/Users/dross/kidney-report-generator/docs/coding-schema.md)

Compatibility note:
- Legacy top-level `classification`, `pattern_metadata`, and `codes` fields remain temporarily readable by the backend during migration, but `coding[]` is the source of truth going forward.
