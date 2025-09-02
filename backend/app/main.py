"""
FastAPI application for Kidney Biopsy Report Generator
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.models.shorthand import ShorthandInput, GeneratedReport, ValidationResponse, LineMapping
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
            return GeneratedReport(report_text="", parsed_data={}, validation_errors=[], line_mappings=[])
        
        # Process character by character, only expanding on word boundaries
        output = []
        line_mappings = []  # Track which code generates which line
        current_token = ""
        current_source_code = ""  # Track the current shorthand code being processed
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
                    current_source_code = current_token.upper()
                    # Check if it's a header
                    if current_token.upper().startswith('!'):
                        expansion = simple_mapper.map_code(current_token.upper())
                        if expansion:
                            # Add blank line before header if not first content
                            if output and output[-1] != '\n':
                                output.append('\n')
                            output.append(expansion)
                        else:
                            output.append(current_token)
                    else:
                        # Regular token - try to expand
                        expansion = simple_mapper.map_code(current_token.upper())
                        output.append(expansion if expansion else current_token)
                    
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
        
        # Build line mappings - parse the generated report to track lines
        # This is a simplified version - in production, track during generation
        lines = report_text.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip():  # Only track non-empty lines
                # For now, we'll add basic tracking
                # In a full implementation, we'd track the actual source codes during generation
                line_mappings.append(LineMapping(
                    line_number=i,
                    source_code="",  # Would be filled during generation
                    original_text=line
                ))
        
        return GeneratedReport(
            report_text=report_text,
            parsed_data={},
            validation_errors=[],
            line_mappings=line_mappings
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
        Dictionary of available phrases
    """
    if report_type not in ["transplant", "native"]:
        raise HTTPException(status_code=400, detail="Invalid report type")
    
    # For now, return transplant phrases
    return template_engine.phrases


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)