"""
Autonomous SAP AI Agent Package.
Provides modular, strongly typed, and decoupled agentic architecture for SAP Business One.
"""
from app.agent.field_mappings import (
    BP_FIELD_MAPPINGS,
    ITEM_FIELD_MAPPINGS,
    MANDATORY_CREATION_SCHEMA,
    WAREHOUSE_FIELD_MAPPINGS,
    normalize_field_name,
    validate_field_value,
)
from app.agent.intent_router import (
    detect_entity,
    detect_intent,
    parse_query_filters,
)
from app.agent.orchestrator import AgentService, agent_service
from app.agent.schemas import (
    AgentChatResult,
    AgentIntent,
    FieldUpdateResult,
    GranularAnswer,
    MissingFieldSpec,
    SAPCreateToolInput,
    SAPEntity,
    SAPGranularAttributeInput,
    SAPQueryToolInput,
    SAPUpdateToolInput,
)
from app.agent.slot_filling import (
    extract_creation_session,
    extract_fields_with_llm,
    parse_creation_fields,
)
import app.agent.specialized_queries as specialized_queries
from app.agent.tools import (
    execute_create_master_data,
    execute_field_update,
    execute_health_check,
    execute_query,
    execute_specific_attribute_query,
    parse_update_request,
    parse_with_llm_fallback,
)

__all__ = [
    "AgentService",
    "agent_service",
    "AgentIntent",
    "SAPEntity",
    "AgentChatResult",
    "FieldUpdateResult",
    "GranularAnswer",
    "MissingFieldSpec",
    "SAPQueryToolInput",
    "SAPUpdateToolInput",
    "SAPCreateToolInput",
    "SAPGranularAttributeInput",
    "BP_FIELD_MAPPINGS",
    "ITEM_FIELD_MAPPINGS",
    "WAREHOUSE_FIELD_MAPPINGS",
    "MANDATORY_CREATION_SCHEMA",
    "normalize_field_name",
    "validate_field_value",
    "detect_intent",
    "detect_entity",
    "parse_query_filters",
    "parse_creation_fields",
    "extract_fields_with_llm",
    "extract_creation_session",
    "parse_update_request",
    "parse_with_llm_fallback",
    "execute_field_update",
    "execute_create_master_data",
    "execute_specific_attribute_query",
    "execute_health_check",
    "execute_query",
    "specialized_queries",
]
