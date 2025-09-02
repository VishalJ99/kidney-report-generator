"""
FastAPI application for Kidney Biopsy Report Generator
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.models.shorthand import ShorthandInput, GeneratedReport, ValidationResponse
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
        import re
        
        shorthand = input_data.shorthand_text
        if not shorthand:
            return GeneratedReport(report_text="", parsed_data={}, validation_errors=[])
        
        # Process line by line to preserve structure
        lines = shorthand.split('\n')
        output_lines = []
        
        for line in lines:
            # Handle @...@ protected blocks
            if '@' in line:
                # Split by @ markers to find protected text
                parts = re.split(r'@([^@]*)@', line)
                processed_parts = []
                
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd indices are inside @ markers
                        # Keep this text exactly as-is
                        processed_parts.append(part)
                    else:  # Even indices are outside @ markers
                        # Process tokens for possible expansion
                        if part.strip():
                            tokens = part.split()
                            expanded_tokens = []
                            
                            for token in tokens:
                                expansion = simple_mapper.map_code(token.upper().strip())
                                if expansion:
                                    # Headers always get blank line before
                                    if token.upper().startswith('!'):
                                        if output_lines:  # Not the very first line
                                            output_lines.append('')  # Blank line
                                        expanded_tokens = [expansion]  # Replace entire line with header
                                        break  # Headers take the whole line
                                    else:
                                        expanded_tokens.append(expansion)
                                else:
                                    # No mapping - keep original token
                                    expanded_tokens.append(token)
                            
                            processed_parts.append(' '.join(expanded_tokens))
                
                output_lines.append(''.join(processed_parts))
            else:
                # No @ markers - process entire line normally
                if not line.strip():
                    output_lines.append('')  # Preserve blank lines
                    continue
                
                tokens = line.split()
                expanded_tokens = []
                
                for token in tokens:
                    expansion = simple_mapper.map_code(token.upper().strip())
                    if expansion:
                        # Headers always get blank line before
                        if token.upper().startswith('!'):
                            if output_lines:  # Not the very first line
                                output_lines.append('')  # Blank line
                            expanded_tokens = [expansion]  # Replace entire line with header
                            break  # Headers take the whole line
                        else:
                            expanded_tokens.append(expansion)
                    else:
                        # No mapping - keep original token
                        expanded_tokens.append(token)
                
                output_lines.append(' '.join(expanded_tokens))
        
        # Join all lines to create final report
        report_text = '\n'.join(output_lines)
        
        return GeneratedReport(
            report_text=report_text,
            parsed_data={},
            validation_errors=[]
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