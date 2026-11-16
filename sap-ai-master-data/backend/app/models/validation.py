"""
Validation result models for deterministic Pydantic backend validation.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MissingFieldInfo(BaseModel):
    field: str
    label: str
    reason: str
    field_type: str = "string"
    example: Optional[str] = None

class ValidationErrorItem(BaseModel):
    field: str
    message: str
    error_type: str = "value_error"
    provided_value: Optional[Any] = None

class ValidationResult(BaseModel):
    valid: bool
    master_type: str
    missing_fields: List[MissingFieldInfo] = Field(default_factory=list)
    invalid_fields: List[ValidationErrorItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_data: Dict[str, Any] = Field(default_factory=dict)
