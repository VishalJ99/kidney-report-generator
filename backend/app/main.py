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
        # Parse the shorthand input
        parsed_data = parser.parse(input_data.shorthand_text)
        
        # Generate the report
        report_text = template_engine.generate_report(parsed_data)
        
        # Return the generated report
        return GeneratedReport(
            report_text=report_text,
            parsed_data=parsed_data,
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