# Kidney Biopsy Report Generator - Codebase Context

## Project Overview
A web application that converts medical shorthand notation into standardized kidney biopsy reports for pathologists. Operates as an "augmented typing" interface where users type naturally and certain shorthand codes automatically expand to full medical phrases.

## Architecture

### Frontend (Next.js + React)
**Location**: `/frontend/`

- **`app/page.tsx`**: Main application page
  - Manages shorthand input state
  - Sends POST requests to `/api/generate` with 500ms debounce
  - Displays generated report in real-time

- **`components/ShorthandInput.tsx`**: Text input component
  - Simple textarea for shorthand entry
  - Shows quick reference hints

- **`components/ReportPreview.tsx`**: Report display component
- **`components/QuickActions.tsx`**: Copy/export buttons
- **`components/PatientInfo.tsx`**: Patient data display

### Backend (FastAPI + Python)
**Location**: `/backend/`

- **`app/main.py`**: FastAPI application entry point
  - `/api/generate` - **UNIFIED** report generation (single mode for all input)
  - `/api/autocomplete` - Direct single-code expansion endpoint
  - `/api/validate` - Code validation endpoint
  - CORS configured for frontend access

- **`app/services/simple_mapper.py`**: Core expansion engine ✨
  - ~50 lines of clean logic
  - Direct O(1) lookups for static codes
  - Regex pattern matching with ~ prefix
  - Case-insensitive processing

- **`app/services/report_formatter.py`**: Report formatting module
  - Handles section organization
  - Manages headers and spacing
  - Clean separation of concerns

- **`app/services/parser.py`**: [DEPRECATED - no longer used]
- **`app/services/template_engine.py`**: [DEPRECATED - replaced by unified mode]

- **`app/models/shorthand.py`**: Pydantic models
  - Request/response data structures
  - Added AutocompleteRequest/Response models

### Data Files
**Location**: `/backend/app/data/`

- **`phrases_transplant.json`**: Original nested phrase mappings (3-4 levels deep)
- **`phrases_flat.json`**: NEW simplified flat mappings
  - ~450 key-value pairs
  - `~` prefix for regex patterns
  - `!` prefix for section headers

### Documentation
- **`/workspace/CLAUDE.md`**: Project requirements and examples
- **`/workspace/prompt.md`**: Refactoring instructions
- **`/workspace/2025_07 For Vishal/Standard phrases - Transplant v2.md`**: Source medical phrases

## Data Flow (Unified Augmented Typing Mode)

1. **User types** in left panel (any mix of shorthand codes and normal text)
2. **Frontend debounces** input (500ms delay)
3. **POST to `/api/generate`** with raw text
4. **Backend processes line-by-line**:
   - Checks for `@...@` protected blocks (preserved exactly)
   - Splits remaining text into tokens
   - Each token checked against mappings:
     - Has mapping → expand to full phrase
     - No mapping → keep original token
   - Headers (`!` prefix) get blank line before them
5. **Frontend displays** the augmented report in real-time

### Key Processing Rules:
- **Everything goes through one pipeline** (no mode detection)
- **Token-level granularity** - each word processed independently
- **Mixed content supported** - codes and normal text coexist naturally
- **Special markers**:
  - `@text@` - Preserve exactly, no expansion
  - `!CODE` - Header with automatic blank line before

## Key Dependencies

### Frontend
- Next.js 13+
- React 18
- Axios for API calls
- Tailwind CSS
- react-hot-toast

### Backend
- FastAPI
- Python 3.10+
- Pydantic for validation
- Standard library (json, re)

## Entry Points
- Frontend dev: `cd frontend && npm run dev` (port 3000)
- Backend dev: `cd backend && uvicorn app.main:app --reload` (port 8000)
- Docker: `docker-compose up`

## Core Business Logic

### Shorthand Mapping Rules
1. **Static mappings**: Direct 1:1 replacement
   - Example: `MM0` → "There is no increase in mesangial matrix."

2. **Variable patterns**: Regex with substitution
   - Example: `TG5` matches `~TG(\d+)` → "Total number of glomeruli: 5"

3. **Section headers**: Marked with `!` prefix
   - Example: `!G` → "GLOMERULI" (as header)

### Key Transformations
- All shorthand normalized to UPPERCASE for matching
- Space delimiter triggers autocomplete
- Headers create new report sections
- Regex groups substitute into templates via `{1}`, `{2}`, etc.

## Configuration
- CORS origins configured in `main.py`
- API URL in frontend: `process.env.NEXT_PUBLIC_API_URL`
- Railway deployment configs present

## Recent Changes (2025-09-02)

### Edit Overlay System Implementation ✅
- **Added bidirectional editing capability** - Users can edit generated reports
- **Edit preservation system** - Edits survive regeneration via overlay pattern
- **Line mapping tracking** - Backend tracks which shorthand generates which line
- **Visual indicators** - Subtle highlighting for edited (amber) and added (green) lines
- **Edit mode toggle** - Switch between view-only and editable modes
- **No emoji approach** - Professional appearance with colored borders instead

## Recent Changes (2025-09-02)

### Unified Augmented Typing Mode ✅
- **Eliminated dual-mode complexity** - everything through single pipeline
- **Token-level processing** - each word checked independently
- **Mixed content support** - codes and normal text coexist
- **Protected text blocks** - `@...@` preserves exact text
- **Automatic header formatting** - blank lines before headers

### Performance Improvements
- **Code reduction**: 250+ lines → ~80 lines (68% reduction)
- **Lookup speed**: O(1) for 90% of codes (static mappings)
- **Single code path** - eliminates special cases
- **Natural typing feel** - type normally, magic words expand

### Architecture Simplification
- Removed dependency on `parser.py`
- Removed dependency on `template_engine.py`
- Single unified processing in `/api/generate`
- Clean separation: expansion (SimpleMapper) vs formatting (inline)

---
*Last Updated: 2025-09-02 - Unified augmented typing mode implemented*