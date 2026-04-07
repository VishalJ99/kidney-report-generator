# AGENTS.md

This file is for new coding agents entering the repository. Read it before making assumptions.

## Objective

The product turns kidney biopsy shorthand into standardized report text that pathologists can paste into downstream systems. The current experience is an augmented typing workflow:

- the user types shorthand and plain text into one textarea
- the frontend regenerates the report preview almost immediately
- the backend expands only completed tokens
- conclusion shorthand can also emit registry/database codes

Primary value is speed and consistency of clinical reporting, not generic document generation.

## Read These First

If you need the current truth fast, start here:

1. `frontend/app/page.tsx`
2. `backend/app/main.py`
3. `backend/app/services/simple_mapper.py`
4. `backend/app/data/phrases_sectioned.json`
5. `docs/core-runtime.md`
6. `docs/architecture.md`

## Current Architecture In One Pass

- Frontend: Next.js 14 app router, single-page UI in `frontend/app/page.tsx`
- Backend: FastAPI app in `backend/app/main.py`
- Core mapping engine: `backend/app/services/simple_mapper.py`
- Phrase source of truth at runtime: `backend/app/data/phrases_sectioned.json`
- Phrase authoring source: `backend/app/data/phrases_flat v4 2026_01_09.xlsx`
- Phrase conversion script: `backend/scripts/convert_excel_to_json.py`
- Local runtime: `docker-compose.yml`
- Hosted runtime intent: Railway configs in the repo root plus service directories

## Restart Direction: April 2026

- `phrases_sectioned.json` is still the canonical runtime dictionary, but the active product direction now includes a frontend-backed write path for adding and updating shorthand entries.
- Phrase entries are section-aware. Each shorthand key can define `main_body`, `conclusion`, and `comments` text independently.
- Code metadata lives under each phrase entry’s `codes` object. The main code families in active use are `native1`, `transplant`, and `kbc`, but legacy keys such as `native2` may still exist and should not be discarded casually.
- A raw code value of `VALUE` means the code has not been assigned yet. Treat it as a placeholder, not as a usable code.
- The frontend should surface all resolved case codes live while the user types, not just a single conclusion-only code.
- Both transplant and native workflows matter now. Do not assume native is still “coming soon” if the runtime code has been updated.

## Shorthand Grammar And Runtime Invariants

- Expansion is stateful and section-aware. Do not treat the input as a flat string replacement pipeline.
- Ordinary shorthand tokens expand only when they hit a hard boundary: space or newline.
- The final in-progress token is intentionally left unexpanded while the user is still typing.
- `@...@` blocks are protected literal text. No shorthand expansion happens inside them.
- Tokens beginning with `!` are structural markers:
  - they can emit visible section-header text
  - they can switch the active section used for later token lookup
- Section context determines whether a phrase uses `main_body`, `conclusion`, or `comments`.
- Code collection is additive metadata gathered during the same completed-token pass as text expansion. It should not alter expansion semantics.

## Golden Path

1. User types shorthand into `ShorthandInput`.
2. `frontend/app/page.tsx` debounces input by 25ms and posts raw text to `POST /api/generate`.
3. `backend/app/main.py` walks the raw text character by character.
4. Expansion only happens when a token reaches a word boundary.
5. `@...@` blocks are preserved verbatim.
6. `!` markers switch section context between `main_body`, `conclusion`, and `comments`.
7. `SimpleMapper.map_code()` does a direct lookup first, then regex matching against `phrases_sectioned.json`.
8. The backend returns `report_text` plus `conclusion_codes` and structured `case_codes`.
9. The frontend shows the report, shows extracted case codes, and supports copy-to-clipboard.
10. The reference modal fetches flat mappings through `GET /api/phrases/{report_type}`, while the phrase manager uses structured read/write endpoints.

## Repo Lay Of The Land

| Area | Purpose | Notes |
| --- | --- | --- |
| `frontend/app/page.tsx` | Main UI and orchestration | This is the real frontend control plane |
| `frontend/components/` | UI pieces | `PatientInfo.tsx` exists but is not currently rendered |
| `frontend/hooks/usePhraseMappings.ts` | Loads reference data | Used by the mapping modal |
| `backend/app/main.py` | API entrypoint | `/api/generate` is the hot path |
| `backend/app/services/simple_mapper.py` | Core mapping engine | Most behavior changes route through here |
| `backend/app/data/phrases_sectioned.json` | Runtime mappings | Section-aware values plus conclusion codes |
| `backend/scripts/convert_excel_to_json.py` | Data regeneration | Use when updating mappings from the workbook |
| `2025_07 For Vishal/` | Domain reference material | Medical phrase and template source docs |
| `docs/architecture.md` | System architecture | High-signal overview for contributors |

## Docs Map

Use these intentionally. They are not all equally current.

| File | Use it for | Reliability |
| --- | --- | --- |
| `docs/core-runtime.md` | Canonical shorthand grammar, parser state model, and runtime/API contracts | High |
| `docs/architecture.md` | Current system topology and runtime flow | High |
| `README.md` | Setup, endpoints, basic project overview | Medium |
| `CLAUDE.md` | Product intent, domain framing, older architecture goals | Medium |
| `context.md` | Historical implementation notes | Low to medium, partially stale |
| `prompt.md` | Refactor history and intended simplification | Low to medium, historical |
| `task_log.md` | Change history from a past refactor | Low to medium, historical |
| `2025_07 For Vishal/...` | Clinical phrase and template source material | High for domain context |

## Known Mismatches And Traps

- `context.md` describes an edit-overlay system with `line_mappings`; the current main page does not use that flow.
- `backend/app/models/shorthand.py` still includes `line_mappings`, but `/api/generate` currently returns the default empty list.
- `backend/app/services/parser.py` and `backend/app/services/template_engine.py` still exist, but the current report-generation hot path does not depend on them.
- `backend/test_example.py` tests the old parser/template pipeline, not the live production path.
- `frontend/next.config.js` has an `/api/*` rewrite, but the page currently calls `NEXT_PUBLIC_API_URL` directly through axios.
- Flat reference endpoints are for lookup UX, not structured phrase editing.
- Runtime JSON writes are live immediately in the backend service, but without persistent Railway storage they will not survive redeploys.
- The working tree often contains generated noise in `frontend/.next/` and Python `__pycache__` directories. Do not mistake that for intentional product work.

## Working Rules For Future Agents

- Treat runtime code and `phrases_sectioned.json` as the canonical behavior.
- If you are changing phrase content at scale, prefer editing the Excel workbook and regenerating JSON with `backend/scripts/convert_excel_to_json.py`.
- If you are changing live expansion behavior, inspect `backend/app/main.py` and `backend/app/services/simple_mapper.py` together.
- If you are changing phrase-management behavior, inspect `frontend/app/page.tsx`, `backend/app/main.py`, and `backend/app/services/simple_mapper.py` together.
- If you are changing live code display behavior, verify whether the backend contract is `conclusion_codes`, broader case-level code metadata, or both before editing the frontend.
- Do not remove legacy files casually. Some are still imported, instantiated, or used by ad hoc scripts.
- If docs disagree with code, trust code and update docs.

## Deployment Notes

- Production is deployed as two Railway services: one frontend service and one backend service.
- Frontend reads `NEXT_PUBLIC_API_URL` directly and talks to the backend over HTTP; keep that contract explicit in docs and deployment changes.
- Runtime writes to `phrases_sectioned.json` take effect immediately in the running backend service.
- Railway container filesystem writes should be treated as runtime-local. Without persistent storage, dictionary edits will not survive a redeploy or rebuild.
- The backend supports `PHRASES_JSON_PATH` so the runtime dictionary can live on a Railway-mounted volume, for example `/data/phrases_sectioned.json`.
- Current production URL reference: `https://enthusiastic-wonder-production.up.railway.app/`

## Useful Commands

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
docker-compose up
python backend/test_simple_mapper.py
python backend/scripts/convert_excel_to_json.py --preview
```
