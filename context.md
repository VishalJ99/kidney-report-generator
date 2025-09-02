# Kidney Biopsy Report Generator - Codebase Context

## Project Overview
A web application that converts medical shorthand notation into standardized kidney biopsy reports for pathologists. Operates as an "augmented typing" interface where users type naturally and certain shorthand codes automatically expand to full medical phrases.

## Architecture

### Frontend (Next.js + React)
**Location**: `/frontend/`

- **`app/page.tsx`**: Main application page
  - Manages shorthand input state
  - Sends POST requests to `/api/generate` with 500ms debounce
  - **NEW**: Edit overlay state management (editOverlay Map, manualAdditions array)
  - **NEW**: `applyEditOverlay()` - Applies preserved edits to regenerated reports
  - **NEW**: `toggleEditMode()` - Switches between view/edit modes
  - **NEW**: `handleReportEdit()` - Processes user edits to report text
  - Displays generated report in real-time with edit preservation

- **`components/ShorthandInput.tsx`**: Text input component
  - Simple textarea for shorthand entry
  - Shows quick reference hints

- **`components/ReportPreview.tsx`**: Report display component
  - **ENHANCED**: Now supports editable mode with textarea
  - **NEW**: Edit mode toggle button
  - **NEW**: Status badges showing edit count
  - **NEW**: Conditional rendering based on edit mode
  - **NEW**: Auto-resize textarea functionality

- **`components/QuickActions.tsx`**: Copy/export buttons
- **`components/PatientInfo.tsx`**: Patient data display

#### New Frontend Modules

- **`types/report.ts`**: TypeScript interfaces for edit system
  - `LineMapping`: Maps line numbers to source shorthand codes
  - `EditEntry`: Tracks original vs edited text per line
  - `ManualAddition`: Tracks user-added text
  - `GeneratedReportResponse`: API response with line mappings

- **`utils/editDetector.ts`**: Edit detection and management
  - `detectEdits()`: Compares original vs edited text, returns overlay
  - `getEditedLineNumbers()`: Identifies edited lines for highlighting
  - `getLineStatus()`: Determines if line is original/edited/added

- **`styles/report.css`**: Visual styling for edit system
  - `.edited-line`: Amber border/background for edited lines
  - `.manual-addition`: Green border/background for added lines
  - `.report-editable`: Textarea styling for edit mode
  - Professional appearance without emojis

### Backend (FastAPI + Python)
**Location**: `/backend/`

- **`app/main.py`**: FastAPI application entry point
  - `/api/generate` - **UNIFIED** report generation (single mode for all input)
    - **ENHANCED**: Now returns `line_mappings` array with each response
    - **NEW**: Tracks which shorthand code generates which line
    - **NEW**: Builds LineMapping objects during report generation
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
  - **NEW**: `LineMapping` model - tracks line_number, source_code, original_text
  - **ENHANCED**: `GeneratedReport` model now includes `line_mappings` field

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

## Data Flow (Unified Augmented Typing Mode with Edit Overlay)

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
   - **NEW**: Builds `line_mappings` array tracking source codes
5. **Frontend receives** report + line mappings
6. **Apply edit overlay** (if exists):
   - Check each line against edit overlay Map
   - Replace with edited version if found
   - Append manual additions at specified positions
7. **Frontend displays** the final report (base + edits)

### Edit Mode Flow

1. **User clicks "Edit Report"** → enters edit mode
2. **Textarea replaces <pre>** → user can edit directly
3. **On edit completion**:
   - `detectEdits()` compares original vs edited
   - Creates edit overlay entries for changed lines
   - Identifies manual additions
4. **User adds more shorthand**:
   - Generate fresh report from backend
   - Apply saved edit overlay
   - New content appends at end
5. **Edits persist** through regeneration cycles

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
*Last Updated: 2025-09-02 - Edit overlay system implemented with bidirectional editing*