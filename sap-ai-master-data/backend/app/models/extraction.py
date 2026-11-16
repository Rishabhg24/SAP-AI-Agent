"""
Extraction models for multi-engine PDF processing and consensus comparison.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MasterDataType(str, Enum):
    ITEM = "item"
    BUSINESS_PARTNER = "business_partner"
    WAREHOUSE = "warehouse"
    UNKNOWN = "unknown"

class ConflictStatus(str, Enum):
    AGREED = "AGREED"
    CONFLICT = "CONFLICT"
    PARTIAL = "PARTIAL"

class SingleExtractorOutput(BaseModel):
    method: str = Field(description="Name of extraction method, e.g., 'pymupdf', 'pdfplumber', 'ocr_layout'")
    success: bool = True
    master_type: MasterDataType = MasterDataType.UNKNOWN
    data: Dict[str, Any] = Field(default_factory=dict)
    records: List[Dict[str, Any]] = Field(default_factory=list)
    raw_text: Optional[str] = None
    extra_fields: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

class FieldComparison(BaseModel):
    field_name: str
    status: ConflictStatus
    agreed_value: Optional[Any] = None
    extracted_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Values extracted by each method: {'pymupdf': val, 'pdfplumber': val, ...}"
    )
    distinct_values: List[Any] = Field(default_factory=list)
    resolved_value: Optional[Any] = None
    is_resolved: bool = False

class ExtractionComparisonResult(BaseModel):
    status: ConflictStatus
    master_type: MasterDataType
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    field_comparisons: Dict[str, FieldComparison] = Field(default_factory=dict)
    agreed_data: Dict[str, Any] = Field(default_factory=dict)
    conflicts: List[FieldComparison] = Field(default_factory=list)
    extra_fields: Dict[str, Any] = Field(default_factory=dict)
    all_records: List[Dict[str, Any]] = Field(default_factory=list)
    total_records: int = 1
