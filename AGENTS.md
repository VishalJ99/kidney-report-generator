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
5. `docs/architecture.md`

## Current Architecture In One Pass

- Frontend: Next.js 14 app router, single-page UI in `frontend/app/page.tsx`
- Backend: FastAPI app in `backend/app/main.py`
- Core mapping engine: `backend/app/services/simple_mapper.py`
- Phrase source of truth at runtime: `backend/app/data/phrases_sectioned.json`
- Phrase authoring source: `backend/app/data/phrases_flat v4 2026_01_09.xlsx`
- Phrase conversion script: `backend/scripts/convert_excel_to_json.py`
- Local runtime: `docker-compose.yml`
- Hosted runtime intent: Railway configs in the repo root plus service directories

## Golden Path

1. User types shorthand into `ShorthandInput`.
2. `frontend/app/page.tsx` debounces input by 25ms and posts raw text to `POST /api/generate`.
3. `backend/app/main.py` walks the raw text character by character.
4. Expansion only happens when a token reaches a word boundary.
5. `@...@` blocks are preserved verbatim.
6. `!` markers switch section context between `main_body`, `conclusion`, and `comments`.
7. `SimpleMapper.map_code()` does a direct lookup first, then regex matching against `phrases_sectioned.json`.
8. The backend returns `report_text` plus `conclusion_codes`.
9. The frontend shows the report, shows extracted conclusion codes, and supports copy-to-clipboard.
10. The reference modal fetches all mappings through `GET /api/phrases/{report_type}`.

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
- `report_type` is present in the API contract, but the UI only exposes transplant; native is not productized end-to-end.
- The working tree often contains generated noise in `frontend/.next/` and Python `__pycache__` directories. Do not mistake that for intentional product work.

## Working Rules For Future Agents

- Treat runtime code and `phrases_sectioned.json` as the canonical behavior.
- If you are changing phrase content at scale, prefer editing the Excel workbook and regenerating JSON with `backend/scripts/convert_excel_to_json.py`.
- If you are changing live expansion behavior, inspect `backend/app/main.py` and `backend/app/services/simple_mapper.py` together.
- Do not remove legacy files casually. Some are still imported, instantiated, or used by ad hoc scripts.
- If docs disagree with code, trust code and update docs.

## Useful Commands

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
docker-compose up
python backend/test_simple_mapper.py
python backend/scripts/convert_excel_to_json.py --preview
```
