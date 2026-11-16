"""
Workflow state machine and audit models.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.extraction import ExtractionComparisonResult, MasterDataType
from app.models.validation import MissingFieldInfo, ValidationResult

class WorkflowStatus(str, Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTION_CONFLICT = "EXTRACTION_CONFLICT"
    EXTRACTED = "EXTRACTED"
    VALIDATING = "VALIDATING"
    MISSING_FIELDS = "MISSING_FIELDS"
    READY_FOR_CONFIRMATION = "READY_FOR_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    CREATING_IN_SAP = "CREATING_IN_SAP"
    CREATED = "CREATED"
    DUPLICATE = "DUPLICATE"
    SAP_ERROR = "SAP_ERROR"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class BulkRecordResult(BaseModel):
    index: int
    code: str
    name: str = ""
    status: str  # "CREATED", "DUPLICATE", "VALIDATION_ERROR", "SAP_ERROR"
    sap_object_id: Optional[str] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None

class BulkCreationSummary(BaseModel):
    total_submitted: int = 0
    created_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0
    records: List[BulkRecordResult] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None

class RecordValidationStatus(BaseModel):
    index: int
    code: str = ""
    name: str = ""
    valid: bool
    missing_fields: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class BulkValidationSummary(BaseModel):
    total: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    missing_fields_summary: List[str] = Field(default_factory=list)
    record_statuses: List[RecordValidationStatus] = Field(default_factory=list)

class WorkflowState(BaseModel):
    workflow_id: str
    filename: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    master_type: MasterDataType = MasterDataType.UNKNOWN
    status: WorkflowStatus = WorkflowStatus.UPLOADED
    message: str = "Workflow initiated"
    
    # Extraction stage
    raw_extractions: Dict[str, Any] = Field(default_factory=dict)
    extraction_comparison: Optional[ExtractionComparisonResult] = None
    normalized_data: Dict[str, Any] = Field(default_factory=dict)
    extracted_records: List[Dict[str, Any]] = Field(default_factory=list)
    total_records: int = 1
    
    # Conflict resolution
    user_corrections: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation stage
    validation_result: Optional[ValidationResult] = None
    missing_fields: List[MissingFieldInfo] = Field(default_factory=list)
    bulk_validation: Optional[BulkValidationSummary] = None
    
    # Pre-creation & Confirmation
    final_payload: Dict[str, Any] = Field(default_factory=dict)
    is_confirmed: bool = False
    
    # SAP response & Audit
    sap_response_status: Optional[int] = None
    sap_object_id: Optional[str] = None
    sap_response_body: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    bulk_results: Optional[BulkCreationSummary] = None
    
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AuditLogRecord(BaseModel):
    id: Optional[int] = None
    workflow_id: Optional[str] = "system"
    master_type: str = "master_data"
    action: str = "CREATE"
    activity: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: Optional[str] = None
    user_identifier: str = "system_user"
    company_db: Optional[str] = None
    transaction_num: Optional[str] = None
    previous_value: Optional[str] = None
    updated_value: Optional[str] = None
    payload_hash: Optional[str] = None
    sap_response_status: Optional[int] = None
    sap_object_id: Optional[str] = None
    success: bool = True
    details: Optional[str] = None

