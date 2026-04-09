# Coding Schema Contract

Implemented under `PER-143` in the Linear project `candice report tool`.

## Why this exists

The project is moving from a single top-level code bucket per shorthand entry to a structure that can support:

- one shorthand expanding to multiple coded concepts
- the same shorthand carrying codes for multiple downstream systems
- explicit modality/source handling for pattern codes
- export logic that can iterate coded concepts without string parsing or special cases

The canonical structure needs to be readable by humans editing JSON, stable for backend processing, and predictable for future export code.

## Canonical structure

Shorthand entries keep their text fields and use a top-level `coding` array for coded concepts:

```json
"example-key": {
  "main_body": "",
  "conclusion": "Example combined finding",
  "comments": "",
  "coding": [
    {
      "classification": "diagnosis",
      "medium": "PATIENT",
      "codes": {
        "kbc": "103",
        "transplant": "TX-001"
      }
    },
    {
      "classification": "pattern",
      "medium": "LM",
      "codes": {
        "kbc": "280",
        "transplant": "t3"
      }
    }
  ]
}
```

## Rules

1. `coding` is the source of truth for coded metadata.
2. Each `coding[]` item is one coded concept that can be looped over independently.
3. Each `coding[]` item has exactly:
   - `classification`: `diagnosis | pattern | attribute`
   - `medium`: `PATIENT | LM | EM | IHC`
   - `codes`: scalar-or-null code values keyed by code system, for example `kbc`, `native1`, `native2`, `transplant`
4. Code-system values inside one `coding[]` item are never lists.
5. `codes["kbc"]` or `codes["transplant"]` always resolves to a single code value when present.
6. Use `null` when a code system has been considered for that coded concept but no code has been provided yet, for example `native1: null`.
7. If one shorthand maps to multiple codes within the same family, represent that as multiple `coding[]` items, not a list inside one `codes` object.

## Medium semantics

- `PATIENT`: patient-level concept, used for diagnosis and attribute entries
- `LM`: light microscopy pattern
- `EM`: electron microscopy pattern
- `IHC`: immunohistochemistry pattern

`medium` is always explicit and never null in the canonical schema.

## Design motivations

### 1. Export logic needs iterable coded concepts

Native and transplant export do not consume shorthand text directly. They consume coded concepts. A `coding[]` array makes export logic iterate over coded concepts rather than reverse-engineering meaning from a flattened dict.

### 2. Scalar codes are easier to reason about than in-field lists

Inside one coding group, `codes["kbc"]` should always be a scalar. That keeps downstream logic simple and predictable. If a shorthand needs two KBC diagnoses, it becomes two coding groups.

Allowing `null` for an explicitly missing system keeps the structure inspectable without turning `codes` values into lists or forcing every downstream consumer to infer whether absence means “not considered” or “considered but not provided”.

### 3. Pattern codes need explicit modality

Pattern codes are not just “pattern yes/no”. The medium matters for interpretation and later export. Making `medium` explicit removes the previous ambiguity around `null` and makes `LM` the concrete default for generic “Pattern of injury”.

### 4. One shorthand may represent more than one coded concept

The shorthand syntax is optimized for typing speed, not for one-to-one ontology mapping. A single shorthand can expand to text that implies multiple diagnoses or multiple coded concepts. The `coding[]` array models that directly.

## Migration and compatibility

The backend still accepts and can read legacy top-level fields during transition:

- `classification`
- `pattern_metadata`
- `codes`

When those legacy fields are present and `coding` is absent, the backend normalizes them into a single canonical coding group at runtime where possible.

This compatibility layer exists so the live UI and hand-edited review files can transition incrementally without breaking the report-generation path.

## Code-family provenance

The code-family names in runtime JSON come from the source workbook rather than from later hand-edited review files.

In particular:
- `native1`
- `native2`
- other workbook-derived code columns

should be treated as source-defined names.

Source:
- [phrases_flat v4 2026_01_09.xlsx](/Users/dross/kidney-report-generator/backend/app/data/phrases_flat%20v4%202026_01_09.xlsx), `CONCLUSION` sheet, row 2

This is important because `native2` can look suspicious when it appears in later review artifacts, but its provenance is older: workbook -> conversion script -> runtime JSON -> mapper logic.
