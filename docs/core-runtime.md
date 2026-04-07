# Core Runtime

This file is the canonical logic spec for the live shorthand-to-report pipeline.

If docs conflict with code, trust:

1. `backend/app/main.py`
2. `backend/app/services/simple_mapper.py`
3. `backend/app/data/phrases_sectioned.json`

## Purpose

The runtime converts a pathologist's shorthand into standardized report text with near-instant feedback while preserving plain text, section structure, and attached diagnostic codes.

The core value is speed and consistency during typing, not batch document generation.

## Hot Path Files

1. `frontend/app/page.tsx`
2. `backend/app/main.py`
3. `backend/app/services/simple_mapper.py`
4. `backend/app/data/phrases_sectioned.json`

## Core Mental Model

The parser is a stateful token walker.

It maintains:

1. an output buffer
2. a current token buffer
3. a current section
4. whether the cursor is inside a protected `@...@` block

The current section starts as `main_body`.

## Grammar Rules

1. Plain text passes through unchanged
- Anything that is not a completed shorthand token is emitted as typed.

2. Expansion only happens at hard boundaries
- A shorthand token expands only when followed by a space or newline.
- The final unfinished token at end of input remains unexpanded.

3. `@...@` blocks are protected literal text
- No shorthand expansion occurs inside a protected block.
- If the block is unclosed at end of input, the leading `@` is preserved.

4. `!` tokens are structural markers
- They can emit visible section-header text.
- They can switch the active section used for subsequent token lookup.

5. Section context controls lookup
- Each shorthand entry can define different values for:
  - `main_body`
  - `conclusion`
  - `comments`
- The same shorthand key can therefore expand differently depending on where it appears.

6. Code collection is additive
- When a completed shorthand token resolves successfully, the backend may also collect diagnostic code metadata from that entry.
- Code collection should not alter text expansion behavior.

## Token Classes

| Token class | Example | Expands text | Changes section | Collects codes |
| --- | --- | --- | --- | --- |
| Ordinary shorthand | `mvi` | Yes, if mapped | No | Yes, if codes exist |
| Structural header | `!conc` | Yes | Yes, for some headers | No |
| Protected block | `@free text@` | No expansion | No | No |
| In-progress token at EOF | `mvi` with no trailing boundary | No | No | No |

## Section Markers

Current known section behavior in the live path:

- `!conc` switches to `conclusion`
- `!com` switches to `comments`
- `!lm`, `!g`, `!t`, `!bv`, `!ihc`, `!ip`, `!ifp`, `!em`, `!iff` switch to or remain in `main_body`

These tokens are not normal diagnosis shorthand. They are part of the typing grammar.

## Phrase Dictionary Contract

The runtime dictionary lives in `backend/app/data/phrases_sectioned.json` unless overridden by `PHRASES_JSON_PATH`.

Each normal entry looks like:

```json
{
  "mpgn-ic": {
    "main_body": "",
    "conclusion": "Membranoproliferative glomerulonephritis, immune complex type (IC-MPGN)",
    "comments": "Long explanatory comment...",
    "codes": {
      "native1": "46826",
      "kbc": "16"
    }
  }
}
```

Meaning:

- `main_body`: text used when current section is `main_body`
- `conclusion`: text used when current section is `conclusion`
- `comments`: text used when current section is `comments`
- `codes`: attached metadata for downstream systems

Important code rules:

- `transplant`, `native1`, and `kbc` are common code families
- unknown existing code keys must be preserved during structured updates
- a raw code value of `VALUE` is a placeholder and should not be emitted as a usable code

## Pattern Entries

Entries whose keys begin with `~` are regex-style pattern mappings.

Behavior:

- direct exact-key lookup happens first
- regex-pattern lookup happens second
- matched capture groups can be substituted into the mapped text

## Runtime Algorithm

Pseudo-flow:

```text
walk input character by character
build current token until boundary

if inside @...@:
  preserve literal content

on space/newline:
  if token starts with !:
    expand header text
    maybe switch current section
  else:
    expand token using current section
    collect any attached code metadata

if final token has no boundary:
  leave it unexpanded
```

## API Contracts

### `POST /api/generate`

Input:

```json
{
  "shorthand_text": "...",
  "report_type": "transplant"
}
```

Runtime expectations:

- drives the live preview
- returns generated report text
- returns conclusion-scoped codes for compatibility
- may also return broader case-level code metadata for the frontend panel

### `GET /api/phrases/{report_type}`

Purpose:

- read-only flattened mapping reference for lookup UX

Important:

- this is not the structured edit contract

### `GET /api/phrases/entries`

Purpose:

- structured phrase-entry list for dictionary management UI

### `PUT /api/phrases/entries/{phrase_key}`

Purpose:

- structured create/update path for runtime dictionary edits

Important:

- updates should preserve unknown existing code keys
- writes should be atomic
- in-memory runtime behavior should reflect the updated dictionary immediately

## Frontend Runtime Expectations

The frontend should assume:

1. typing in the shorthand textarea triggers near-immediate regeneration
2. the backend is the source of truth for section-aware expansion
3. code display is derived from backend response metadata, not frontend re-parsing
4. dictionary editing is separate from the typing workflow

## Persistence Model

Local default:

- bundled JSON file in the repo

Railway runtime intent:

- backend service mounts a persistent volume
- `PHRASES_JSON_PATH` points to the dictionary on that volume
- example path: `/data/phrases_sectioned.json`

Without persistent storage, runtime edits survive only until rebuild or redeploy.

## Safe vs Unsafe Changes

Safe to change:

- dead legacy code not on the active request path
- additive code-collection metadata
- structured phrase-management APIs
- frontend UI around reference and phrase management
- documentation when it diverges from code

Unsafe to change casually:

- boundary-based expansion semantics
- section switching via `!` markers
- `@...@` protected text behavior
- section-aware lookup order
- regex fallback behavior

## Legacy Traps

- `backend/app/services/parser.py` is not the live runtime path
- `backend/app/services/template_engine.py` is not the live runtime path
- `backend/test_example.py` targets an older pipeline
- `line_mappings` exists in models but is not currently meaningful in the live hot path

## Change Checklist For Future Agents

Before editing runtime behavior, confirm:

1. Which section state transitions are relied on?
2. Whether the change affects expansion timing at token boundaries?
3. Whether codes should be conclusion-only or case-level?
4. Whether the frontend is consuming flat reference mappings or structured phrase entries?
5. Whether dictionary writes must survive Railway redeploys?
