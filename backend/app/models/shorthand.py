"""
Pydantic models for shorthand input and output
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class LineMapping(BaseModel):
    """Model for tracking which shorthand code generated which line"""
    line_number: int = Field(..., description="Line number in the generated report (1-indexed)")
    source_code: str = Field(..., description="The shorthand code that generated this line")
    original_text: str = Field(..., description="The original generated text for this line")


class ShorthandInput(BaseModel):
    """Model for shorthand input from frontend"""
    shorthand_text: str = Field(..., description="Raw shorthand text input")
    report_type: str = Field(default="transplant", description="Type of report (transplant or native)")


class GeneratedReport(BaseModel):
    """Model for generated report output"""
    report_text: str = Field(..., description="Generated report text")
    parsed_data: Dict[str, Any] = Field(..., description="Parsed structured data")
    validation_errors: list = Field(default=[], description="Any validation errors found")
    line_mappings: List[LineMapping] = Field(default=[], description="Mapping of lines to source shorthand codes")
    

class ValidationResponse(BaseModel):
    """Model for code validation response"""
    is_valid: bool = Field(..., description="Whether all codes are valid")
    invalid_codes: list = Field(default=[], description="List of invalid codes")
    suggestions: Dict[str, list] = Field(default={}, description="Suggestions for invalid codes")