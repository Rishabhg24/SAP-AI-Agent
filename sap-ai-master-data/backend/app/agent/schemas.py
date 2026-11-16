"""
Structured Pydantic Schemas for Autonomous SAP AI Agent.
Defines strong typing for intents, entity models, slot-filling drafts,
query filters, update payloads, and LLM tool calling definitions.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AgentIntent(str, Enum):
    QUERY = "QUERY"
    UPDATE = "UPDATE"
    CREATE_DRAFT = "CREATE_DRAFT"
    CREATE_READY = "CREATE_READY"
    CREATE_SUCCESS = "CREATE_SUCCESS"
    CREATE_FAILED = "CREATE_FAILED"
    CONFIRM_CREATE = "CONFIRM_CREATE"
    SPECIFIC_QUERY = "SPECIFIC_QUERY"
    SPECIALIZED_QUERY = "SPECIALIZED_QUERY"
    HEALTH = "HEALTH"
    EXPLAIN = "EXPLAIN"


class SAPEntity(str, Enum):
    BUSINESS_PARTNERS = "BusinessPartners"
    ITEMS = "Items"
    WAREHOUSES = "Warehouses"


class MissingFieldSpec(BaseModel):
    field: str
    label: str
    example: Optional[str] = ""
    reason: Optional[str] = ""
    max_length: Optional[int] = None
    mandatory: bool = True


class GranularAnswer(BaseModel):
    attribute: str
    value: str
    code: str
    name: str


class FieldUpdateResult(BaseModel):
    key: str
    entity: str
    updated_fields: Dict[str, Any]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    hash: Optional[str] = None


class AgentChatResult(BaseModel):
    success: bool = True
    status: str = "SUCCESS"
    reply: str
    action: str = "EXPLAIN"
    entity: Optional[str] = None
    records: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    update_result: Optional[Dict[str, Any]] = None
    creation_draft: Optional[Dict[str, Any]] = None
    missing_fields: List[Dict[str, Any]] = Field(default_factory=list)
    is_creation_ready: bool = False
    granular_answer: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
    prompt: Optional[str] = None
    query_type: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


# ============================================================================
# Structured LLM Tool Calling Schemas (Compatible with OpenAI / LangChain)
# ============================================================================

class SAPQueryToolInput(BaseModel):
    """Query SAP Business One master records with filters and sorting."""
    entity: SAPEntity = Field(..., description="Target SAP entity (BusinessPartners, Items, Warehouses)")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Field-value filters or thresholds (e.g. {'City': 'Mumbai', 'Balance__gt': 1000})")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of records to retrieve")


class SAPUpdateToolInput(BaseModel):
    """Update single or multiple fields on an allowlisted SAP record."""
    entity: SAPEntity = Field(..., description="Target SAP entity (BusinessPartners, Items, Warehouses)")
    key: str = Field(..., description="Primary identifier (CardCode, ItemCode, or WarehouseCode)")
    fields: Dict[str, Any] = Field(..., description="Key-value mapping of SAP fields to update")


class SAPCreateToolInput(BaseModel):
    """Create a new master data record in SAP Business One."""
    entity: SAPEntity = Field(..., description="Target SAP entity (BusinessPartners, Items, Warehouses)")
    data: Dict[str, Any] = Field(..., description="Validated creation payload conforming to mandatory schema")


class SAPGranularAttributeInput(BaseModel):
    """Retrieve a specific single attribute of a target SAP master record."""
    entity: SAPEntity = Field(..., description="Target SAP entity")
    target_code_or_name: str = Field(..., description="Code or name of the record")
    attribute: str = Field(..., description="Target field to retrieve (e.g. Address, TaxRate, Stock, Phone)")
