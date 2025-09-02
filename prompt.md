# Kidney Biopsy Report Autocomplete Refactoring

## Overview
This document outlines the refactoring needed to simplify the shorthand-to-longform autocomplete logic for the kidney biopsy reporting system.

## Current Implementation Problems

### 1. Complex Backend Architecture
**Location**: `backend/app/services/`

- **`template_engine.py` (Lines 135-391)**: Contains 9 separate processing methods:
  - `_process_light_microscopy()`
  - `_process_glomeruli()`
  - `_process_tubulointerstitium()`
  - `_process_blood_vessels()`
  - `_process_immunohistochemistry()`
  - `_process_electron_microscopy()`
  - `_process_immunofluorescence()`
  - `_process_conclusion()`
  - `_process_comment()`
  
  Each method has 10-30+ hardcoded conditions with regex patterns mixed with direct lookups.

- **`parser.py` (Lines 107-164)**: Complex compound code parsing with multiple regex patterns for special cases.

- **`phrases_transplant.json`**: Nested 3-4 levels deep with inconsistent structure.

### 2. Current Flow
1. User types shorthand in textarea
2. **Real-time processing** (when `autoGenerate` is enabled):
   - useEffect with 500ms debounce triggers after typing stops
   - Sends ENTIRE shorthand text to `/api/generate`
   - Backend processes ALL codes at once
   - Returns complete report and updates preview
3. Manual processing (when `autoGenerate` is disabled):
   - User clicks "Generate Report" button
   - Same backend processing as above

### 3. Issues
- **Batch processing instead of incremental**: Processes entire text every 500ms rather than individual codes
- **No code-by-code feedback**: Can't see what each code expands to as you type
- **Inefficient**: Re-processes everything on each keystroke (after debounce)
- Complex section-dependent logic
- Difficult to maintain/extend
- ~250 lines of processing logic that could be ~50 lines

## New Simplified Approach

### 1. New Data Structure
**File**: `backend/app/data/phrases_flat.json` (already created)

A flat JSON with ~450 key-value pairs:
- **Static mappings**: Direct lookups (e.g., `"MM0": "There is no increase in mesangial matrix."`)
- **Regex patterns**: Prefixed with `~` (e.g., `"~TG(\\d+)": "Total number of glomeruli: {1}"`)
- **Section headers**: Prefixed with `!` (e.g., `"!G": "GLOMERULI"`)

### 2. New Processing Logic

#### Simple Mapper Class
```python
class SimpleMapper:
    def __init__(self):
        with open('phrases_flat.json') as f:
            self.mappings = json.load(f)
    
    def map_code(self, code):
        # Normalize to uppercase
        code = code.upper()
        
        # Try direct lookup first
        if code in self.mappings:
            return self.mappings[code]
        
        # Try regex patterns
        for key, template in self.mappings.items():
            if key.startswith('~'):
                pattern = key[1:]  # Remove ~
                match = re.match(pattern, code)
                if match:
                    # Substitute groups into template
                    result = template
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f'{{{i}}}', group)
                    return result
        
        return None  # No match found
```

### 3. Incremental Autocomplete Flow (Proposed Enhancement)

#### Frontend Changes Needed
**Location**: `frontend/components/ShorthandInput.tsx` and `frontend/app/page.tsx`

Current: Single textarea with batch processing (entire text sent every 500ms)
New: Incremental autocomplete on space delimiter (process each code individually)

```javascript
// Pseudocode for new approach
const handleShorthandChange = (text) => {
    const tokens = text.split(' ');
    const lastToken = tokens[tokens.length - 1];
    
    if (lastToken && !text.endsWith(' ')) {
        // User still typing current token
        return;
    }
    
    if (tokens.length > 1) {
        const previousToken = tokens[tokens.length - 2];
        // Send to autocomplete API
        const expanded = await autocomplete(previousToken);
        if (expanded) {
            // Add to report preview
            updateReport(expanded);
        }
    }
};
```

#### Backend Changes Needed
**New endpoint**: `/api/autocomplete`

```python
@app.post("/api/autocomplete")
async def autocomplete(code: str):
    mapper = SimpleMapper()
    result = mapper.map_code(code)
    return {"code": code, "expansion": result}
```

### 4. Section Formatting Module

Separate module for handling sections and formatting:

```python
class ReportFormatter:
    def format_entries(self, entries):
        """
        entries = [
            {"type": "header", "text": "GLOMERULI"},
            {"type": "content", "text": "Total number of glomeruli: 5"},
            ...
        ]
        """
        formatted = []
        for entry in entries:
            if entry["type"] == "header":
                formatted.append(f"\n{entry['text']}\n")
            else:
                formatted.append(entry['text'])
        return '\n'.join(formatted)
```

## Refactoring Tasks

### Phase 1: Backend Simplification
1. **Create `simple_mapper.py`**
   - Load `phrases_flat.json`
   - Implement `map_code()` method with uppercase normalization
   - Handle static lookups and regex patterns

2. **Add `/api/autocomplete` endpoint**
   - Accept single code
   - Return expanded text or null

3. **Keep existing `/api/generate` for backward compatibility**
   - Refactor to use SimpleMapper internally
   - Process multiple codes in sequence

### Phase 2: Frontend Enhancement
1. **Update `ShorthandInput.tsx`**
   - Add real-time change handler
   - Detect space delimiter
   - Call autocomplete API

2. **Update `page.tsx`**
   - Add state for incremental report building
   - Update report preview in real-time
   - Keep manual "Generate Report" as fallback

### Phase 3: Formatting Module
1. **Create `report_formatter.py`**
   - Handle section headers (! prefix)
   - Format report structure
   - Maintain proper spacing and organization

### Phase 4: Cleanup
1. **Remove old complex logic**
   - Delete 9 processing methods from `template_engine.py`
   - Simplify `parser.py`
   - Archive old `phrases_transplant.json`

## Testing Strategy

1. **Unit tests for SimpleMapper**
   - Test all static mappings
   - Test all regex patterns
   - Test uppercase normalization

2. **Integration tests**
   - Test autocomplete endpoint
   - Test full report generation
   - Compare output with old system

3. **Frontend tests**
   - Test real-time autocomplete
   - Test section formatting
   - Test edge cases (typos, unknown codes)

## Benefits of Refactoring

1. **Simplicity**: ~50 lines instead of ~250 lines
2. **Maintainability**: Single flat JSON to update
3. **Performance**: O(1) lookups for most codes
4. **User Experience**: Real-time feedback
5. **Extensibility**: Easy to add new codes
6. **Testability**: Simple pure functions

## Migration Notes

- The system should maintain backward compatibility during transition
- Old reports should still generate correctly
- Consider A/B testing the new autocomplete feature
- Keep the old batch processing as a fallback option

## Key Files to Modify

1. `/backend/app/services/` - Add `simple_mapper.py`
2. `/backend/app/main.py` - Add `/api/autocomplete` endpoint
3. `/frontend/components/ShorthandInput.tsx` - Add real-time handler
4. `/frontend/app/page.tsx` - Update state management
5. `/backend/app/services/template_engine.py` - Refactor to use SimpleMapper

## Success Criteria

1. All existing shorthand codes work correctly
2. Real-time autocomplete responds in <100ms
3. Code complexity reduced by >70%
4. All existing reports generate identically
5. New codes can be added by updating JSON only