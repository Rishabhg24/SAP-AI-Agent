"""
Chat and conversational data collection models.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.validation import MissingFieldInfo

class ChatMessage(BaseModel):
    role: str = Field(description="'user', 'assistant', or 'system'")
    content: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatRequest(BaseModel):
    workflow_id: Optional[str] = None
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    history: Optional[List[Any]] = None

class ChatResponse(BaseModel):
    reply: str
    workflow_id: Optional[str] = None
    extracted_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-values extracted from user reply to update master data"
    )
    missing_fields: List[MissingFieldInfo] = Field(default_factory=list)
    validation_status: Optional[str] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
