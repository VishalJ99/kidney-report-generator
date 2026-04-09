"""
Pydantic models for shorthand input, phrase management, and report output.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

PhraseClassification = Literal["diagnosis", "pattern", "attribute"]
CodeMedium = Literal["PATIENT", "LM", "EM", "IHC"]


class LineMapping(BaseModel):
    """Model for tracking which shorthand code generated which line."""

    line_number: int = Field(..., description="Line number in the generated report (1-indexed)")
    source_code: str = Field(..., description="The shorthand code that generated this line")
    original_text: str = Field(..., description="The original generated text for this line")


class ShorthandInput(BaseModel):
    """Model for shorthand input from frontend."""

    shorthand_text: str = Field(..., description="Raw shorthand text input")
    report_type: str = Field(default="transplant", description="Type of report (transplant or native)")


class CodingGroup(BaseModel):
    """A single coded concept associated with a shorthand entry."""

    classification: PhraseClassification = Field(..., description="Classification for this coded concept")
    medium: CodeMedium = Field(..., description="Medium/source for this coded concept")
    codes: Dict[str, str] = Field(
        default_factory=dict,
        description="Single code per code system for this coded concept",
    )


class PhraseEntryPayload(BaseModel):
    """Structured phrase payload for create/update operations."""

    main_body: str = Field(default="", description="Expansion used in the main body section")
    conclusion: str = Field(default="", description="Expansion used in the conclusion section")
    comments: str = Field(default="", description="Expansion used in the comments section")
    coding: List[CodingGroup] = Field(
        default_factory=list,
        description="Canonical coded concepts for the shorthand entry",
    )
    classification: Optional[PhraseClassification] = Field(
        default=None,
        description="Legacy compatibility field derived from or convertible into coding",
    )
    pattern_metadata: Optional[Dict[str, Optional[CodeMedium]]] = Field(
        default=None,
        description="Legacy compatibility field derived from or convertible into coding",
    )
    codes: Dict[str, str] = Field(
        default_factory=dict,
        description="Legacy compatibility field derived from or convertible into coding",
    )


class PhraseEntryResponse(PhraseEntryPayload):
    """Structured phrase entry returned to the frontend."""

    key: str = Field(..., description="Normalized shorthand key")


class ConclusionCode(BaseModel):
    """Model for extracted primary conclusion codes."""

    key: str = Field(..., description="The shorthand key entered")
    code: str = Field(..., description="The database code for this key")


class CaseCode(BaseModel):
    """Model for all code-bearing shorthand detected in the case."""

    key: str = Field(..., description="The shorthand key entered")
    section: str = Field(..., description="Section where the shorthand was entered")
    label: str = Field(..., description="Human-readable label for the shorthand entry")
    coding: List[CodingGroup] = Field(
        default_factory=list,
        description="Canonical coded concepts resolved for this shorthand entry",
    )
    classification: Optional[PhraseClassification] = Field(
        default=None,
        description="Legacy compatibility field derived from coding where possible",
    )
    pattern_metadata: Optional[Dict[str, Optional[CodeMedium]]] = Field(
        default=None,
        description="Legacy compatibility field derived from coding where possible",
    )
    codes: Dict[str, str] = Field(default_factory=dict, description="All non-empty resolved codes for the entry")
    pending_code_types: List[str] = Field(
        default_factory=list,
        description="Code families present as unresolved placeholders such as VALUE",
    )


class GeneratedReport(BaseModel):
    """Model for generated report output."""

    report_text: str = Field(..., description="Generated report text")
    parsed_data: Dict[str, Any] = Field(default_factory=dict, description="Parsed structured data")
    validation_errors: List[str] = Field(default_factory=list, description="Any validation errors found")
    line_mappings: List[LineMapping] = Field(default_factory=list, description="Mapping of lines to source shorthand codes")
    conclusion_codes: List[ConclusionCode] = Field(default_factory=list, description="Extracted codes from conclusion section")
    case_codes: List[CaseCode] = Field(default_factory=list, description="All detected code-bearing shorthand entries")


class ValidationResponse(BaseModel):
    """Model for code validation response."""

    is_valid: bool = Field(..., description="Whether all codes are valid")
    invalid_codes: List[str] = Field(default_factory=list, description="List of invalid codes")
    suggestions: Dict[str, List[str]] = Field(default_factory=dict, description="Suggestions for invalid codes")


PhraseEntry = PhraseEntryResponse
PhraseEntryUpdate = PhraseEntryPayload
