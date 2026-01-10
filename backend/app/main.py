"""
FastAPI application for Kidney Biopsy Report Generator
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.models.shorthand import ShorthandInput, GeneratedReport, ValidationResponse, ConclusionCode
from app.services.parser import ShorthandParser
from app.services.template_engine import TemplateEngine
from app.services.simple_mapper import SimpleMapper
from pydantic import BaseModel, Field
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Kidney Biopsy Report Generator",
    description="API for generating kidney biopsy reports from shorthand notation",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
parser = ShorthandParser()
template_engine = TemplateEngine()
simple_mapper = SimpleMapper()

# Autocomplete models
class AutocompleteRequest(BaseModel):
    """Request model for autocomplete endpoint"""
    code: str = Field(..., description="Single shorthand code to expand")

class AutocompleteResponse(BaseModel):
    """Response model for autocomplete endpoint"""
    code: str = Field(..., description="Original shorthand code")
    expansion: Optional[str] = Field(None, description="Expanded medical phrase")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Kidney Biopsy Report Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/api/generate",
            "validate": "/api/validate",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "kidney-report-generator"}


@app.post("/api/generate", response_model=GeneratedReport)
async def generate_report(input_data: ShorthandInput):
    """
    Generate a kidney biopsy report from shorthand notation

    Args:
        input_data: ShorthandInput containing the shorthand text

    Returns:
        GeneratedReport with the formatted report text
    """
    try:
        shorthand = input_data.shorthand_text
        if not shorthand:
            return GeneratedReport(report_text="", parsed_data={}, validation_errors=[], conclusion_codes=[])

        # Section header mapping - which headers switch to which section
        section_headers = {
            '!conc': 'conclusion',
            '!com': 'comments',
            # All these stay in/switch to main_body
            '!lm': 'main_body',
            '!g': 'main_body',
            '!t': 'main_body',
            '!bv': 'main_body',
            '!ihc': 'main_body',
            '!ip': 'main_body',
            '!ifp': 'main_body',
            '!em': 'main_body',
            '!iff': 'main_body',
        }

        # Track current section and conclusion keys
        current_section = "main_body"
        conclusion_keys = []

        # Process character by character, only expanding on word boundaries
        output = []
        current_token = ""
        in_protected_block = False
        protected_content = ""

        i = 0
        while i < len(shorthand):
            char = shorthand[i]

            # Handle @ markers
            if char == '@':
                if in_protected_block:
                    # Check if there's a space or newline after closing @
                    next_char = shorthand[i+1] if i+1 < len(shorthand) else ''
                    if next_char in [' ', '\n'] or next_char == '':
                        # Confirmed closed block - hide @ markers
                        output.append(protected_content)
                        protected_content = ""
                        in_protected_block = False
                        i += 1  # Skip the @
                        if next_char:
                            output.append(next_char)
                            i += 1  # Skip the space/newline
                        continue
                    else:
                        # Not followed by boundary - treat as literal @
                        protected_content += char
                else:
                    # Opening @ or standalone @
                    # First, process any pending token
                    if current_token:
                        output.append(current_token)  # Don't expand incomplete tokens
                        current_token = ""

                    # Start protected block
                    in_protected_block = True
                    protected_content = ""

            elif in_protected_block:
                # Inside @ block - just accumulate, never expand
                protected_content += char

            elif char in [' ', '\n']:
                # Word boundary - check for expansion
                if current_token:
                    token_lower = current_token.lower()

                    # Check if it's a header (starts with !)
                    if token_lower.startswith('!'):
                        # Expand header using main_body (headers are defined there)
                        expansion = simple_mapper.map_code(current_token, section="main_body")
                        if expansion:
                            # Add blank line before header if not first content
                            if output and output[-1] != '\n':
                                output.append('\n')
                            output.append(expansion)
                        else:
                            output.append(current_token)

                        # Update section AFTER expanding header
                        if token_lower in section_headers:
                            current_section = section_headers[token_lower]
                    else:
                        # Regular token - try to expand with section context
                        expansion = simple_mapper.map_code(current_token, section=current_section)
                        output.append(expansion if expansion else current_token)

                        # Track keys entered in conclusion section for code extraction
                        if current_section == "conclusion":
                            conclusion_keys.append(token_lower)

                    current_token = ""

                # Add the space or newline
                output.append(char)

            else:
                # Regular character - accumulate token
                current_token += char

            i += 1

        # Handle any remaining content
        if in_protected_block:
            # Unclosed @ block - show everything including @
            output.append('@' + protected_content)
        elif current_token:
            # Last token without space - don't expand (still typing)
            output.append(current_token)

        report_text = ''.join(output)

        # Extract conclusion codes
        extracted_codes = []
        for key in conclusion_keys:
            code = simple_mapper.get_conclusion_code(key, input_data.report_type)
            if code:
                extracted_codes.append(ConclusionCode(key=key, code=code))

        return GeneratedReport(
            report_text=report_text,
            parsed_data={},
            validation_errors=[],
            conclusion_codes=extracted_codes
        )

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_codes(input_data: ShorthandInput):
    """
    Validate shorthand codes without generating a full report
    
    Args:
        input_data: ShorthandInput containing the shorthand text
        
    Returns:
        ValidationResponse with validation results
    """
    try:
        # Parse the shorthand input
        parsed_data = parser.parse(input_data.shorthand_text)
        
        # TODO: Implement comprehensive validation
        # For now, return success
        return ValidationResponse(
            is_valid=True,
            invalid_codes=[],
            suggestions={}
        )
        
    except Exception as e:
        logger.error(f"Error validating codes: {str(e)}")
        return ValidationResponse(
            is_valid=False,
            invalid_codes=[],
            suggestions={}
        )


@app.post("/api/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    """
    Convert a single shorthand code to its full medical phrase.
    This replaces the complex 250+ line processing with a simple lookup.
    
    Args:
        request: AutocompleteRequest containing a single shorthand code
        
    Returns:
        AutocompleteResponse with the expanded phrase or None if not found
    """
    try:
        expansion = simple_mapper.map_code(request.code)
        return AutocompleteResponse(
            code=request.code,
            expansion=expansion
        )
    except Exception as e:
        logger.error(f"Error in autocomplete: {str(e)}")
        return AutocompleteResponse(
            code=request.code,
            expansion=None
        )


@app.get("/api/phrases/{report_type}")
async def get_phrases(report_type: str):
    """
    Get available phrase mappings for a report type

    Args:
        report_type: Type of report (transplant or native)

    Returns:
        Dictionary of available phrases with section labels
        Format: { "key [SECTION]": "value", ... }
    """
    if report_type not in ["transplant", "native"]:
        raise HTTPException(status_code=400, detail="Invalid report type")

    # Return mappings with section labels for reference popup
    return simple_mapper.get_all_mappings()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)