"""
Pydantic models for shorthand input and output
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ShorthandInput(BaseModel):
    """Model for shorthand input from frontend"""
    shorthand_text: str = Field(..., description="Raw shorthand text input")
    report_type: str = Field(default="transplant", description="Type of report (transplant or native)")


class GeneratedReport(BaseModel):
    """Model for generated report output"""
    report_text: str = Field(..., description="Generated report text")
    parsed_data: Dict[str, Any] = Field(..., description="Parsed structured data")
    validation_errors: list = Field(default=[], description="Any validation errors found")
    

class ValidationResponse(BaseModel):
    """Model for code validation response"""
    is_valid: bool = Field(..., description="Whether all codes are valid")
    invalid_codes: list = Field(default=[], description="List of invalid codes")
    suggestions: Dict[str, list] = Field(default={}, description="Suggestions for invalid codes")