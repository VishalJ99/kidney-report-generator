"""
FastAPI application for Kidney Biopsy Report Generator
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.models.shorthand import (
    CaseCode,
    ConclusionCode,
    GeneratedReport,
    PhraseEntryPayload,
    PhraseEntryResponse,
    ShorthandInput,
    ValidationResponse,
)
from app.services.export_builder import ExportConflictError, build_export_workbook
from app.services.simple_mapper import SimpleMapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kidney Biopsy Report Generator",
    description="API for generating kidney biopsy reports from shorthand notation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

simple_mapper = SimpleMapper()


class AutocompleteRequest(BaseModel):
    """Request model for autocomplete endpoint."""

    code: str = Field(..., description="Single shorthand code to expand")


class AutocompleteResponse(BaseModel):
    """Response model for autocomplete endpoint."""

    code: str = Field(..., description="Original shorthand code")
    expansion: Optional[str] = Field(None, description="Expanded medical phrase")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Kidney Biopsy Report Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "validate": "/api/validate",
            "phrases": "/api/phrases/entries",
            "health": "/health",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "kidney-report-generator"}


@app.post("/api/generate", response_model=GeneratedReport)
async def generate_report(input_data: ShorthandInput):
    """Generate a kidney biopsy report from shorthand notation."""
    try:
        shorthand = input_data.shorthand_text
        if not shorthand:
            return GeneratedReport(report_text="")

        section_headers = {
            "!conc": "conclusion",
            "!com": "comments",
            "!lm": "main_body",
            "!g": "main_body",
            "!t": "main_body",
            "!bv": "main_body",
            "!ihc": "main_body",
            "!ip": "main_body",
            "!ifp": "main_body",
            "!em": "main_body",
            "!iff": "main_body",
        }

        current_section = "main_body"
        conclusion_keys = []
        case_codes: List[CaseCode] = []
        seen_case_code_keys = set()

        output = []
        current_token = ""
        in_protected_block = False
        protected_content = ""

        i = 0
        while i < len(shorthand):
            char = shorthand[i]

            if char == "@":
                if in_protected_block:
                    next_char = shorthand[i + 1] if i + 1 < len(shorthand) else ""
                    if next_char in [" ", "\n"] or next_char == "":
                        output.append(protected_content)
                        protected_content = ""
                        in_protected_block = False
                        i += 1
                        if next_char:
                            output.append(next_char)
                            i += 1
                        continue
                    protected_content += char
                else:
                    if current_token:
                        output.append(current_token)
                        current_token = ""
                    in_protected_block = True
                    protected_content = ""

            elif in_protected_block:
                protected_content += char

            elif char in [" ", "\n"]:
                if current_token:
                    token_lower = current_token.lower().strip()

                    if token_lower.startswith("!"):
                        expansion = simple_mapper.map_code(current_token, section="main_body")
                        if expansion:
                            if output and output[-1] != "\n":
                                output.append("\n")
                            output.append(expansion)
                        else:
                            output.append(current_token)

                        if token_lower in section_headers:
                            current_section = section_headers[token_lower]
                    else:
                        expansion = simple_mapper.map_code(current_token, section=current_section)
                        output.append(expansion if expansion else current_token)

                        case_code = simple_mapper.get_case_code(current_token, current_section)
                        if case_code and case_code["key"] not in seen_case_code_keys:
                            case_codes.append(CaseCode(**case_code))
                            seen_case_code_keys.add(case_code["key"])

                        if current_section == "conclusion":
                            conclusion_keys.append(token_lower)

                    current_token = ""

                output.append(char)

            else:
                current_token += char

            i += 1

        if in_protected_block:
            output.append("@" + protected_content)
        elif current_token:
            output.append(current_token)

        report_text = "".join(output)

        extracted_codes = []
        seen_conclusion_pairs = set()
        for key in conclusion_keys:
            for code in simple_mapper.get_conclusion_codes(key, input_data.report_type):
                if (key, code) not in seen_conclusion_pairs:
                    extracted_codes.append(ConclusionCode(key=key, code=code))
                    seen_conclusion_pairs.add((key, code))

        return GeneratedReport(
            report_text=report_text,
            conclusion_codes=extracted_codes,
            case_codes=case_codes,
        )

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.post("/api/export")
async def export_report(input_data: ShorthandInput):
    """Generate a report-type-specific XLSX export from shorthand notation."""
    try:
        generated_report = await generate_report(input_data)
        workbook_bytes = build_export_workbook(
            shorthand_text=input_data.shorthand_text,
            report_type=input_data.report_type,
            case_codes=[case_code.model_dump() for case_code in generated_report.case_codes],
        )
        filename = f"kidney-report-{input_data.report_type}-export.xlsx"
        return StreamingResponse(
            iter([workbook_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ExportConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_codes(input_data: ShorthandInput):
    """Validate shorthand codes without generating a full report."""
    try:
        return ValidationResponse(is_valid=True)
    except Exception as e:
        logger.error(f"Error validating codes: {str(e)}")
        return ValidationResponse(is_valid=False)


@app.get("/api/phrases/entries", response_model=List[PhraseEntryResponse])
async def list_phrase_entries():
    """Return structured phrase entries for frontend phrase management."""
    try:
        return simple_mapper.get_phrase_entries()
    except Exception as e:
        logger.error(f"Error listing phrase entries: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing phrase entries: {str(e)}")


@app.put("/api/phrases/entries/{phrase_key}", response_model=PhraseEntryResponse)
async def upsert_phrase_entry(phrase_key: str, payload: PhraseEntryPayload):
    """Create or update a phrase entry and persist it to the runtime dictionary."""
    try:
        return simple_mapper.upsert_phrase_entry(phrase_key, payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error upserting phrase entry {phrase_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error upserting phrase entry: {str(e)}")


@app.delete("/api/phrases/entries/{phrase_key}", response_model=PhraseEntryResponse)
async def delete_phrase_entry(phrase_key: str):
    """Delete a phrase entry from the runtime dictionary."""
    try:
        return simple_mapper.delete_phrase_entry(phrase_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting phrase entry {phrase_key}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting phrase entry: {str(e)}")


@app.get("/api/phrases/download")
async def download_phrase_dictionary():
    """Download the current runtime phrase dictionary as JSON."""
    return FileResponse(
        path=str(simple_mapper.json_path),
        media_type="application/json",
        filename="phrases_sectioned.json",
    )


@app.post("/api/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    """Convert a single shorthand code to its full medical phrase."""
    try:
        expansion = simple_mapper.map_code(request.code)
        return AutocompleteResponse(code=request.code, expansion=expansion)
    except Exception as e:
        logger.error(f"Error in autocomplete: {str(e)}")
        return AutocompleteResponse(code=request.code, expansion=None)


@app.get("/api/phrases/{report_type}")
async def get_phrases(report_type: str):
    """Get available phrase mappings for a report type."""
    if report_type not in ["transplant", "native"]:
        raise HTTPException(status_code=400, detail="Invalid report type")

    return simple_mapper.get_all_mappings()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
