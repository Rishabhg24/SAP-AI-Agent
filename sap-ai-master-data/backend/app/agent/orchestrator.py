"""
Autonomous SAP AI Agent Orchestrator.
Coordinates deterministic fast-path execution, interactive multi-turn slot filling,
compliance queries, and LLM fallback routing.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.agent.field_mappings import (
    BP_FIELD_MAPPINGS,
    ITEM_FIELD_MAPPINGS,
    MANDATORY_CREATION_SCHEMA,
    WAREHOUSE_FIELD_MAPPINGS,
    normalize_field_name as _normalize_field_name,
    validate_field_value as _validate_field_value,
)
from app.agent.intent_router import (
    detect_entity as _detect_entity,
    detect_intent as _detect_intent,
    parse_query_filters as _parse_query_filters,
)
from app.agent.slot_filling import (
    extract_creation_session as _extract_creation_session,
    extract_fields_with_llm as _extract_fields_with_llm,
    parse_creation_fields as _parse_creation_fields,
)
import app.agent.specialized_queries as sq
from app.agent.tools import (
    execute_create_master_data as _execute_create_master_data,
    execute_field_update as _execute_field_update,
    execute_health_check as _execute_health_check,
    execute_query as _execute_query,
    execute_specific_attribute_query as _execute_specific_attribute_query,
    parse_update_request as _parse_update_request,
    parse_with_llm_fallback as _parse_with_llm_fallback,
    resolve_granular_query_with_llm as _resolve_granular_query_with_llm,
)
from app.config import settings
from app.services.chat_service import nvidia_chat_service
from app.utils.logging import logger


UPDATE_FIELD_DESCRIPTORS: Dict[str, Dict[str, Any]] = {
    "Phone1": {"label": "Phone Number", "example": "9876543210", "reason": "New primary contact phone number"},
    "GSTNo": {"label": "GST Number (GSTIN)", "example": "27AABCU9603R1ZM", "reason": "15-digit statutory GSTIN (or 'UNREGISTERED')"},
    "PANNo": {"label": "PAN Number", "example": "AABCU9603R", "reason": "10-digit Permanent Account Number"},
    "EmailAddress": {"label": "Email Address", "example": "accounts@company.com", "reason": "Official billing email address"},
    "CardName": {"label": "Company / Partner Name", "example": "Zen Steel Industries Ltd", "reason": "Legal entity name in SAP"},
    "Address": {"label": "Registered Address", "example": "Plot 12, Industrial Area, Pune", "reason": "Physical billing address"},
    "City": {"label": "City", "example": "Pune", "reason": "City name"},
    "State": {"label": "State Code", "example": "MH", "reason": "Two-letter state jurisdiction"},
    "ZipCode": {"label": "Zip / Postal Code", "example": "411001", "reason": "Postal pin code"},
    "ItemName": {"label": "Item Name / Description", "example": "High Tensile Hex Bolt M12", "reason": "Catalog description of the item"},
    "Price": {"label": "Unit Price", "example": "250.00", "reason": "Item price in base currency"},
    "TaxRate": {"label": "Tax Rate (%)", "example": "18%", "reason": "Applicable GST/VAT tax percentage"},
    "InventoryUOM": {"label": "Unit of Measure (UoM)", "example": "PCS", "reason": "Base inventory stocking unit"},
    "WarehouseName": {"label": "Warehouse Name", "example": "Central Logistics Hub", "reason": "Facility descriptive title"},
    "HSN": {"label": "HSN / SAC Code", "example": "73181500", "reason": "Harmonized tariff classification code"},
}


def _get_field_descriptor(entity: str, field_name: str) -> Dict[str, Any]:
    if field_name in UPDATE_FIELD_DESCRIPTORS:
        return UPDATE_FIELD_DESCRIPTORS[field_name]
    schema = MANDATORY_CREATION_SCHEMA.get(entity, {}).get(field_name)
    if schema:
        return schema
    return {"label": field_name, "example": "", "reason": f"New value for {field_name}"}


class AgentService:
    """
    Unified Autonomous SAP AI Agent Service.
    Maintains clean class-method interface for total backward compatibility.
    """

    @staticmethod
    def normalize_field_name(entity: str, raw_field: str) -> Optional[str]:
        return _normalize_field_name(entity, raw_field)

    @staticmethod
    def validate_field_value(entity: str, field_name: str, value: Any) -> Tuple[bool, Any, Optional[str]]:
        return _validate_field_value(entity, field_name, value)

    @staticmethod
    def detect_intent(message: str) -> str:
        return _detect_intent(message)

    @staticmethod
    def detect_entity(message: str) -> str:
        return _detect_entity(message)

    @classmethod
    def parse_query_filters(cls, entity: str, message: str) -> Dict[str, Any]:
        return _parse_query_filters(entity, message)

    @classmethod
    def parse_creation_fields(cls, message: str, entity: str) -> Tuple[Dict[str, Any], List[str]]:
        return _parse_creation_fields(message, entity)

    @classmethod
    async def extract_fields_with_llm(cls, message: str, entity: str) -> Dict[str, Any]:
        return await _extract_fields_with_llm(message, entity)

    @classmethod
    async def extract_creation_session(
        cls,
        history: Optional[List[Dict[str, Any]]],
        current_message: str
    ) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], bool, List[str]]:
        return await _extract_creation_session(history, current_message)

    @classmethod
    async def execute_create_master_data(cls, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return await _execute_create_master_data(entity, data)

    @classmethod
    def parse_update_request(
        cls,
        message: str,
        entity_hint: Optional[str] = None,
        key_hint: Optional[str] = None,
        field_hint: Optional[str] = None
    ) -> Tuple[str, Optional[str], Dict[str, Any], Optional[str], List[str]]:
        return _parse_update_request(message, entity_hint, key_hint, field_hint)

    @classmethod
    async def parse_with_llm_fallback(cls, message: str) -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
        return await _parse_with_llm_fallback(message)

    @classmethod
    async def execute_field_update(
        cls,
        entity: str,
        key: str,
        fields: Dict[str, Any],
        prompt: str = ""
    ) -> Dict[str, Any]:
        return await _execute_field_update(entity, key, fields, prompt)

    @classmethod
    async def resolve_granular_query_with_llm(cls, message: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        return await _resolve_granular_query_with_llm(message)

    @classmethod
    async def execute_specific_attribute_query(cls, message: str) -> Optional[Dict[str, Any]]:
        return await _execute_specific_attribute_query(message)

    @classmethod
    async def execute_health_check(cls) -> Dict[str, Any]:
        return await _execute_health_check()

    @classmethod
    async def execute_query(cls, message: str) -> Dict[str, Any]:
        entity = cls.detect_entity(message)
        return await _execute_query(message, entity)

    @classmethod
    async def execute_specialized_query(cls, message: str) -> Optional[Dict[str, Any]]:
        return await sq.execute_specialized_query(message)

    # Specialized Query Aliases
    @classmethod
    async def execute_active_items(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_active_items(message)

    @classmethod
    async def execute_missing_hsn_or_uom(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_missing_hsn_or_uom(message)

    @classmethod
    async def execute_duplicate_items(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_duplicate_items(message)

    @classmethod
    async def execute_items_last_30_days(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_items_last_30_days(message)

    @classmethod
    async def execute_inactive_items_with_stock(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_inactive_items_with_stock(message)

    @classmethod
    async def execute_items_warehouse_stock(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_items_warehouse_stock(message)

    @classmethod
    async def execute_min_max_items(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_min_max_items(message)

    @classmethod
    async def execute_ordered_committed_items(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_ordered_committed_items(message)

    @classmethod
    async def execute_active_customers_vendors(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_active_customers_vendors(message)

    @classmethod
    async def execute_incomplete_bp_master(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_incomplete_bp_master(message)

    @classmethod
    async def execute_duplicate_bp(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_duplicate_bp(message)

    @classmethod
    async def execute_bp_last_30_days(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_bp_last_30_days(message)

    @classmethod
    async def execute_missing_incorrect_gstin_pan(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_missing_incorrect_gstin_pan(message)

    @classmethod
    async def execute_vendors_missing_terms_bank(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_vendors_missing_terms_bank(message)

    @classmethod
    async def execute_inactive_bp_with_balance(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_inactive_bp_with_balance(message)

    @classmethod
    async def execute_overdue_aging_bp(cls, message: str) -> Dict[str, Any]:
        return await sq.execute_overdue_aging_bp(message)

    @classmethod
    async def handle_message(
        cls,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience alias for process_chat."""
        return await cls.process_chat(message=message, history=history)

    @classmethod
    async def process_chat(
        cls,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main Conversational AI Agent orchestrator with Token Minimization & Slot-Filling Engine.
        """
        m_lower = message.strip().lower()
        intent = cls.detect_intent(message)

        last_assistant_turn: Optional[Dict[str, Any]] = None
        active_creation_draft: bool = False
        active_update_turn: Optional[Dict[str, Any]] = None
        hint_key: Optional[str] = None
        hint_entity: Optional[str] = None
        hint_field: Optional[str] = None
        hint_target_fields: List[str] = []
        hint_pending_fields: Dict[str, Any] = {}

        if history:
            for turn in reversed(history):
                if turn.get("role") == "assistant":
                    last_assistant_turn = turn
                    break

            if last_assistant_turn:
                if last_assistant_turn.get("action") == "CREATE_DRAFT" and not last_assistant_turn.get("is_creation_ready"):
                    active_creation_draft = True

                if last_assistant_turn.get("action") == "UPDATE" and not last_assistant_turn.get("update_result"):
                    active_update_turn = last_assistant_turn
                    hint_key = last_assistant_turn.get("target_key")
                    hint_entity = last_assistant_turn.get("entity")
                    hint_field = last_assistant_turn.get("target_field")
                    hint_target_fields = last_assistant_turn.get("target_fields") or []
                    hint_pending_fields = last_assistant_turn.get("pending_fields") or {}
                    if not hint_field and hint_target_fields:
                        hint_field = hint_target_fields[0]
                    if not hint_key:
                        reply_text = str(last_assistant_turn.get("reply", "")) + " " + str(last_assistant_turn.get("content", ""))
                        m_k = re.search(r"\b([CVL]\d{3,6}|ITM-?[A-Za-z0-9_-]+|WH-[A-Za-z0-9_-]+|\d{1,4})\b", reply_text, re.IGNORECASE)
                        if m_k:
                            hint_key = m_k.group(1).upper()

        # 1. Primary Autonomous ReAct Agent Engine (100% Dynamic Model Generation)
        # All messages (greetings, creations, confirmations, queries, updates) are handled dynamically by the AI model.
        if settings.is_nvidia_configured:
            try:
                from app.agent.react_agent import react_agent
                react_res = await react_agent.run(message=message, history=history)
                if react_res and react_res.get("reply"):
                    return react_res
            except Exception as e_react:
                logger.warning(f"Autonomous ReAct Agent exception: {e_react}. Falling back to dynamic pipeline.")

        # 3. Check for Specific Attribute Query FIRST (Deterministic Fallback)
        if intent == "SPECIFIC_QUERY":
            specific_res = await cls.execute_specific_attribute_query(message)
            if specific_res and specific_res.get("success"):
                return specific_res

        # 3. Health Check Intent
        if intent == "HEALTH":
            return await cls.execute_health_check()

        # 4. Universal Field Update Intent on Existing Records or Active Update Session
        is_update_intent = (intent == "UPDATE") or (
            active_update_turn is not None
            and intent in ["EXPLAIN", "QUERY"]
            and not any(kw in m_lower for kw in ["list all", "top 20", "give me top", "sap health", "hi", "hello", "help", "who are you", "create", "add new", "register new"])
        )

        if is_update_intent:
            entity_u, key_u, fields_u, field_u, target_fields_u = cls.parse_update_request(
                message,
                entity_hint=hint_entity,
                key_hint=hint_key,
                field_hint=hint_field
            )

            # Check if this is an update to an active creation draft FIRST (only if not targeting an existing record key)
            if not key_u and active_creation_draft:
                entity, draft, missing_fields, is_ready, val_errors = await cls.extract_creation_session(history, message)
                entity_label = "Business Partner" if entity == "BusinessPartners" else ("Item" if entity == "Items" else "Warehouse")

                error_bullet = ""
                if val_errors:
                    error_bullet = "⚠️ **Please note:**\n" + "\n".join([f"• {e}" for e in val_errors]) + "\n\n"

                if is_ready:
                    filled_summary = [f"• **{k}**: `{v}`" for k, v in draft.items() if v is not None and str(v) != ""]
                    reply = (
                        f"{error_bullet}🎉 **All required details for {entity_label} have been verified and collected!**\n\n"
                        f"**Summary of Record Ready to Post:**\n"
                        + "\n".join(filled_summary)
                        + f"\n\n👉 Click **'Post to SAP'** below to post this record directly to the SAP Service Layer."
                    )
                    return {
                        "success": True,
                        "reply": reply,
                        "action": "CREATE_READY",
                        "entity": entity,
                        "creation_draft": draft,
                        "missing_fields": [],
                        "is_creation_ready": True,
                        "suggestions": []
                    }
                else:
                    missing_list = "\n".join([f"• **{m['label']}** (`{m['field']}`) — *e.g. `{m['example']}`*" for m in missing_fields])
                    collected_lines = [f"• **{k}**: `{v}`" for k, v in draft.items() if v is not None and str(v).strip() != ""]
                    reply = (
                        f"{error_bullet}Draft updated! Details so far for this **{entity_label}**:\n"
                        + "\n".join(collected_lines)
                        + f"\n\n📋 **Please provide the remaining mandatory field{'s' if len(missing_fields) > 1 else ''}:**\n"
                        + missing_list
                    )
                    return {
                        "success": True,
                        "reply": reply,
                        "action": "CREATE_DRAFT",
                        "entity": entity,
                        "creation_draft": draft,
                        "missing_fields": missing_fields,
                        "is_creation_ready": False,
                        "suggestions": []
                    }

            # Inherit and merge active update session state from history
            if active_update_turn:
                if not key_u and hint_key:
                    key_u = hint_key
                if hint_pending_fields:
                    combined_f = dict(hint_pending_fields)
                    combined_f.update(fields_u)
                    fields_u = combined_f
                if hint_target_fields:
                    target_fields_u = list(dict.fromkeys(hint_target_fields + target_fields_u))

            # If user provided a direct standalone value for an expected field during an active update turn
            if active_update_turn and not fields_u and target_fields_u and len(target_fields_u) == 1 and key_u:
                cand_val = message.strip().strip("'\"")
                norm_cand_field = cls.normalize_field_name(entity_u, cand_val)
                if norm_cand_field:
                    target_fields_u = [norm_cand_field]
                elif not any(verb in m_lower for verb in ["change", "update", "set", "modify", "edit", "alter"]):
                    is_v, n_val, _ = cls.validate_field_value(entity_u, target_fields_u[0], cand_val)
                    if is_v:
                        fields_u[target_fields_u[0]] = n_val
                        target_fields_u = []

            # If still nothing found, try LLM fallback
            if not key_u and not target_fields_u and not fields_u:
                llm_entity, llm_key, llm_fields = await cls.parse_with_llm_fallback(message)
                if llm_key:
                    entity_u = llm_entity or entity_u or hint_entity
                    key_u = llm_key
                    for k_name, k_val in llm_fields.items():
                        norm = cls.normalize_field_name(entity_u, k_name) or k_name
                        fields_u[norm] = k_val

            entity_label = "Business Partner" if entity_u == "BusinessPartners" else ("Item" if entity_u == "Items" else "Warehouse")
            code_label = "CardCode" if entity_u == "BusinessPartners" else ("ItemCode" if entity_u == "Items" else "WarehouseCode")

            # Check if key was captured in fields_u or direct standalone message
            if not key_u:
                if code_label in fields_u:
                    key_u = str(fields_u.pop(code_label)).strip()
                else:
                    clean_msg = message.strip().strip("'\"")
                    m_direct = re.match(r"^([CVL]\d{3,6}|ITM-?[A-Za-z0-9_-]+|WH-[A-Za-z0-9_-]+|\d{1,4})$", clean_msg, re.IGNORECASE)
                    if m_direct:
                        key_u = m_direct.group(1).upper()

            # Determine remaining target fields that still need a value
            missing_target_fields = [f for f in target_fields_u if f not in fields_u or fields_u[f] is None or str(fields_u[f]).strip() == ""]

            # Case A: Record key is MISSING (must ask for target record code + any missing fields)
            if not key_u:
                missing_specs = []
                if entity_u == "BusinessPartners":
                    missing_specs.append({
                        "field": "CardCode",
                        "label": "Customer / Vendor Code (CardCode)",
                        "example": "C20000",
                        "reason": "Unique primary key of the Business Partner to update in SAP",
                        "mandatory": True
                    })
                elif entity_u == "Items":
                    missing_specs.append({
                        "field": "ItemCode",
                        "label": "Item Code / SKU (ItemCode)",
                        "example": "ITM-001",
                        "reason": "Unique inventory identifier of the Item to update in SAP",
                        "mandatory": True
                    })
                else:
                    missing_specs.append({
                        "field": "WarehouseCode",
                        "label": "Warehouse Code (WarehouseCode)",
                        "example": "01",
                        "reason": "Unique warehouse identifier to update in SAP",
                        "mandatory": True
                    })

                for mf in missing_target_fields:
                    schema_info = _get_field_descriptor(entity_u, mf)
                    missing_specs.append({
                        "field": mf,
                        "label": schema_info.get("label", mf),
                        "example": schema_info.get("example", ""),
                        "reason": schema_info.get("reason", f"New value for {mf}"),
                        "mandatory": True
                    })

                missing_lines = "\n".join([f"• **{m['label']}** (`{m['field']}`) — *e.g. `{m['example']}`*" for m in missing_specs])

                collected_info = ""
                if fields_u:
                    collected_lines = [f"• **{k}**: `{v}`" for k, v in fields_u.items() if v is not None and str(v).strip() != ""]
                    if collected_lines:
                        collected_info = "Values captured so far:\n" + "\n".join(collected_lines) + "\n\n"

                reply = (
                    f"🔧 **Update {entity_label} Details**\n\n"
                    f"{collected_info}"
                    f"Please provide the missing details to update the record in SAP:\n"
                    + missing_lines
                    + f"\n\n💬 *You can reply with all values together (e.g. `{code_label} C20000, phone 9876543210, GST 27AABCU9603R1ZM`), or one by one.*"
                )
                return {
                    "success": True,
                    "reply": reply,
                    "action": "UPDATE",
                    "entity": entity_u,
                    "target_key": None,
                    "target_field": target_fields_u[0] if target_fields_u else None,
                    "target_fields": target_fields_u,
                    "pending_fields": fields_u,
                    "missing_fields": missing_specs,
                    "is_creation_ready": False,
                    "suggestions": [
                        f"{code_label} is C20000" if entity_u == "BusinessPartners" else f"{code_label} is ITM-001",
                        f"Give me top 20 {entity_label.lower()}s"
                    ]
                }

            # Case B: Key is KNOWN, but some requested target fields are still missing values
            if missing_target_fields:
                missing_specs = []
                for mf in missing_target_fields:
                    schema_info = _get_field_descriptor(entity_u, mf)
                    missing_specs.append({
                        "field": mf,
                        "label": schema_info.get("label", mf),
                        "example": schema_info.get("example", ""),
                        "reason": schema_info.get("reason", f"New value for {mf}"),
                        "mandatory": True
                    })

                missing_lines = "\n".join([f"• **{m['label']}** (`{m['field']}`) — *e.g. `{m['example']}`*" for m in missing_specs])

                collected_info = ""
                if fields_u:
                    collected_lines = [f"• **{k}**: `{v}`" for k, v in fields_u.items() if v is not None and str(v).strip() != ""]
                    if collected_lines:
                        collected_info = "Values captured so far:\n" + "\n".join(collected_lines) + "\n\n"

                reply = (
                    f"🔧 **Update Details for {entity_label} `{key_u}`**\n\n"
                    f"Target {entity_label} **`{key_u}`** identified!\n\n"
                    f"{collected_info}"
                    f"Please provide the new value{'s' if len(missing_specs) > 1 else ''} to apply:\n"
                    + missing_lines
                    + f"\n\n💬 *Reply with the new details (e.g. `Phone 9876543210, GST 27AABCU9603R1ZM`).*"
                )
                return {
                    "success": True,
                    "reply": reply,
                    "action": "UPDATE",
                    "entity": entity_u,
                    "target_key": key_u,
                    "target_field": target_fields_u[0] if target_fields_u else None,
                    "target_fields": target_fields_u,
                    "pending_fields": fields_u,
                    "missing_fields": missing_specs,
                    "is_creation_ready": False,
                    "suggestions": [
                        f"Show details of {key_u}",
                        "Cancel update"
                    ]
                }

            # Case C: Key is KNOWN and fields_u has values to update!
            if fields_u:
                return await cls.execute_field_update(entity=entity_u, key=key_u, fields=fields_u, prompt=message)

            # Case D: Key is KNOWN, but user didn't mention which field to update
            return {
                "success": False,
                "reply": (
                    f"I detected {entity_label} **`{key_u}`**, but didn't identify which field to change.\n\n"
                    f"Which field would you like to update? For example:\n"
                    f"• *'update phone to 9876543210 and GST to 27AABCU9603R1ZM for {key_u}'*\n"
                    f"• *'change address to Pune for {key_u}'*"
                ),
                "action": "UPDATE",
                "entity": entity_u,
                "target_key": key_u,
                "suggestions": [
                    f"Show details of {key_u}",
                    f"Give me top 20 {entity_label.lower()}s"
                ]
            }

        # 5. Interactive Conversational Creation & Slot-Filling
        is_explicit_query = any(kw in m_lower for kw in ["list all", "top ", "give me top", "show all", "search ", "how many", "all items", "all customers", "all warehouses", "all business partners"])
        if (active_creation_draft and not is_explicit_query) or intent == "CREATE":
            # Check for compound request: creation + update to a distinct existing SAP record
            # e.g. "create customer ABC with code C101 and update phone of C20000 to 9876543210"
            compound_update_reply = ""
            upd_match = re.search(r"\b(?:and\s+)?(?:update|change|set)\s+(?:the\s+)?([a-zA-Z0-9\s_]+?)\s+of\s+([A-Za-z0-9_-]+)\s+to\s+([A-Za-z0-9@.+_-]+)\b", message, re.IGNORECASE)
            if upd_match:
                upd_field_raw, upd_target_key, upd_val = upd_match.groups()
                upd_target_key = upd_target_key.strip().upper()
                if upd_target_key and re.match(r"^[CVL]\d{3,6}$", upd_target_key):
                    try:
                        exists = await SAPBusinessPartnersService.check_card_exists(upd_target_key)
                        if exists:
                            norm_f = cls.normalize_field_name("BusinessPartners", upd_field_raw) or "Phone1"
                            is_v, n_val, _ = cls.validate_field_value("BusinessPartners", norm_f, upd_val)
                            if is_v:
                                upd_res = await cls.execute_field_update(entity="BusinessPartners", key=upd_target_key, fields={norm_f: n_val}, prompt=message)
                                if upd_res.get("success"):
                                    compound_update_reply = f"✅ **Updated Existing Record (`{upd_target_key}`)**: {norm_f} updated to `{n_val}` in SAP.\n\n"
                    except Exception as e_upd:
                        logger.debug(f"Compound update check note: {e_upd}")

            entity, draft, missing_fields, is_ready, val_errors = await cls.extract_creation_session(history, message)
            entity_label = "Business Partner" if entity == "BusinessPartners" else ("Item" if entity == "Items" else "Warehouse")

            error_bullet = ""
            if val_errors:
                error_bullet = "⚠️ **Please note:**\n" + "\n".join([f"• {e}" for e in val_errors]) + "\n\n"

            if is_ready:
                filled_summary = [f"• **{k}**: `{v}`" for k, v in draft.items() if v is not None and str(v) != ""]
                reply = (
                    f"{compound_update_reply}{error_bullet}🎉 **All required details for {entity_label} have been verified and collected!**\n\n"
                    f"**Summary of Record Ready to Post:**\n"
                    + "\n".join(filled_summary)
                    + f"\n\n👉 Click **'Post to SAP'** below to post this record directly to the SAP Service Layer."
                )
                return {
                    "success": True,
                    "reply": reply,
                    "action": "CREATE_READY",
                    "entity": entity,
                    "creation_draft": draft,
                    "missing_fields": [],
                    "is_creation_ready": True,
                    "suggestions": ["Post to SAP"]
                }
            else:
                missing_fields_names = [m['field'] for m in missing_fields]
                if entity == "BusinessPartners":
                    type_val = draft.get("CardType")
                    type_label = "Customer" if type_val == "cCustomer" else ("Vendor / Supplier" if type_val == "cSupplier" else None)
                    collected_lines = [f"• **{k}**: `{v}`" for k, v in draft.items() if v is not None and str(v).strip() != ""]
                    collected_summary = ("\n\n📌 **Details noted so far:**\n" + "\n".join(collected_lines)) if collected_lines else ""

                    if not draft:
                        reply = (
                            f"{compound_update_reply}{error_bullet}I'd be glad to help you create a new **Business Partner** in SAP Business One! 🤝\n\n"
                            f"To get started, please provide the key details:\n"
                            f"1. **Business Partner Type**: Is this a **Customer** or a **Vendor / Supplier**?\n"
                            f"2. **Business / Company Name**: What is the company name? *(e.g. `Cinntra Global Logistics Ltd`)*\n"
                            f"3. **Partner Code**: What code should we assign? *(e.g. `C20099` for customer or `V10099` for vendor)*\n\n"
                            f"💬 *You can reply with all details at once, or answer step-by-step. You can also include phone number, address, or GST!*"
                        )
                        suggestions = [
                            "It is a Customer",
                            "It is a Vendor",
                            "Code is C20099",
                            "Code is V10099"
                        ]
                    elif type_label and not draft.get("CardCode") and not draft.get("CardName"):
                        reply = (
                            f"{compound_update_reply}{error_bullet}I'll help you register a new **{type_label}** in SAP Business One! 🤝\n\n"
                            f"Could you please provide:\n"
                            f"1. **{type_label} Code** (`CardCode` — *e.g. `{'C20099' if type_val == 'cCustomer' else 'V10099'}`*)\n"
                            f"2. **Business Name** (`CardName` — *e.g. `Cinntra Global Logistics Ltd`*)\n\n"
                            f"💬 *Feel free to also include phone number or address!*"
                        )
                        suggestions = [
                            f"Code is {'C20099' if type_val == 'cCustomer' else 'V10099'}",
                            "Company name is Cinntra Global",
                            "Phone is 9876543210"
                        ]
                    elif "CardType" in missing_fields_names and "CardCode" not in missing_fields_names and "CardName" not in missing_fields_names:
                        name_val = draft.get('CardName', 'this partner')
                        code_val = draft.get('CardCode', '')
                        reply = (
                            f"{compound_update_reply}{error_bullet}Got it! I've noted down the details so far for this **Business Partner**:\n"
                            f"• **CardCode**: `{code_val}`\n"
                            f"• **CardName**: `{name_val}`\n\n"
                            f"👉 Is this partner a **Customer** or a **Vendor / Supplier** in SAP?"
                        )
                        suggestions = [
                            "It is a Customer",
                            "It is a Vendor"
                        ]
                    elif "CardName" in missing_fields_names and "CardCode" not in missing_fields_names and "CardType" not in missing_fields_names:
                        code_val = draft.get('CardCode')
                        reply = (
                            f"{compound_update_reply}{error_bullet}Got it! I've noted the code **`{code_val}`**"
                            + (f" for this **{type_label}**" if type_label else "")
                            + f".{collected_summary}\n\n"
                            f"👉 Could you please provide the **Business / Company Name** (`CardName`)?"
                        )
                        suggestions = [
                            "Company name is Cinntra Global Logistics",
                            "Name is Apex Industrial Ltd"
                        ]
                    elif "CardCode" in missing_fields_names and "CardName" not in missing_fields_names and "CardType" not in missing_fields_names:
                        name_val = draft.get('CardName')
                        reply = (
                            f"{compound_update_reply}{error_bullet}Noted the company name **'{name_val}'**"
                            + (f" ({type_label})" if type_label else "")
                            + f".{collected_summary}\n\n"
                            f"👉 What **Partner Code** (`CardCode`) would you like to assign? *(e.g. `{'C20099' if type_val == 'cCustomer' else 'V10099'}`)*"
                        )
                        suggestions = [
                            f"CardCode is {'C20099' if type_val == 'cCustomer' else 'V10099'}",
                            "Use code C50001",
                            "Use code V50001"
                        ]
                    elif "CardCode" not in missing_fields_names and ("CardName" in missing_fields_names or "CardType" in missing_fields_names):
                        code_val = draft.get('CardCode')
                        reply = (
                            f"{compound_update_reply}{error_bullet}Got it! I've noted the code **`{code_val}`** for this Business Partner.\n\n"
                            f"👉 Please provide the remaining required details:\n"
                            f"1. **Business Partner Type** (`CardType`): Is this a **Customer** or a **Vendor / Supplier**?\n"
                            f"2. **Business / Company Name** (`CardName` — *e.g. `Cinntra Global Logistics Ltd`*)"
                        )
                        suggestions = [
                            "It is a Customer",
                            "It is a Vendor",
                            "Company name is Cinntra Global"
                        ]
                    else:
                        missing_list = "\n".join([f"• **{m['label']}** (`{m['field']}`) — *e.g. `{m['example']}`*" for m in missing_fields])
                        reply = (
                            f"{compound_update_reply}{error_bullet}Got it! Details noted so far for this **{entity_label}**:\n"
                            + "\n".join(collected_lines)
                            + f"\n\n📋 **Please provide the remaining detail{'s' if len(missing_fields) > 1 else ''}:**\n"
                            + missing_list
                            + f"\n\n💬 *You can reply with all details at once, or enter each field step-by-step.*"
                        )
                        suggestions = [f"{m['label']} is {m['example']}" for m in missing_fields[:3] if m.get('example')]
                else:
                    missing_list = "\n".join([f"• **{m['label']}** (`{m['field']}`) — *e.g. `{m['example']}`*" for m in missing_fields])
                    if not draft:
                        reply = (
                            f"{compound_update_reply}{error_bullet}I'd be glad to help you register a new **{entity_label}** in SAP! ✨\n\n"
                            f"Please provide the required details:\n"
                            + missing_list
                            + f"\n\n💬 *You can reply with all details at once, or enter each field step-by-step.*"
                        )
                    else:
                        collected_lines = [f"• **{k}**: `{v}`" for k, v in draft.items() if v is not None and str(v).strip() != ""]
                        reply = (
                            f"{compound_update_reply}{error_bullet}Got it! I've noted down the details so far for this **{entity_label}**:\n"
                            + "\n".join(collected_lines)
                            + f"\n\n📋 **Please provide the remaining field{'s' if len(missing_fields) > 1 else ''}:**\n"
                            + missing_list
                            + f"\n\n💬 *You can reply with all details at once, or enter each field step-by-step.*"
                        )
                    suggestions = [f"{m['label']} is {m['example']}" for m in missing_fields[:3] if m.get('example')]

                return {
                    "success": True,
                    "reply": reply,
                    "action": "CREATE_DRAFT",
                    "entity": entity,
                    "creation_draft": draft,
                    "missing_fields": missing_fields,
                    "is_creation_ready": False,
                    "suggestions": suggestions
                }

        # 6. Master Data Query Intent
        if intent == "QUERY":
            return await cls.execute_query(message)

        # 7. Check for Specific Attribute Query fallback
        specific_res = await cls.execute_specific_attribute_query(message)
        if specific_res and specific_res.get("success"):
            return specific_res

        # 8. Conversational Fallback with concise token-efficient response
        m_lower = message.strip().lower()
        if any(w in m_lower for w in ["bye", "goodbye", "cya", "see you", "farewell", "exit", "quit", "good night", "take care"]):
            dyn_suggestions = ["Hello again", "Check SAP Health", "Top 20 Items from SAP"]
        elif any(w in m_lower for w in ["hi", "hello", "hey", "hola", "namaste", "good morning", "good evening", "good afternoon"]):
            dyn_suggestions = ["Give me top 20 Business Partners", "Top 20 Items from SAP", "Create a Business Partner", "Check SAP Health"]
        elif any(w in m_lower for w in ["thank", "thanks", "thx", "appreciate", "ok", "okay"]):
            dyn_suggestions = ["Give me top 20 Business Partners", "Top 20 Items from SAP", "Check SAP Health"]
        elif any(w in m_lower for w in ["item", "product", "sku", "inventory"]):
            dyn_suggestions = ["Top 20 Items from SAP", "Create an Item", "What is the tax rate of item ITM-001?"]
        elif any(w in m_lower for w in ["partner", "customer", "vendor", "supplier", "bp"]):
            dyn_suggestions = ["Give me top 20 Business Partners", "Create a Business Partner", "What is the address of customer C20000?"]
        elif any(w in m_lower for w in ["warehouse", "wh"]):
            dyn_suggestions = ["List all Warehouses", "Create a Warehouse", "Where is warehouse 01 located?"]
        else:
            dyn_suggestions = ["Give me top 20 Business Partners", "Top 20 Items from SAP", "Create a Business Partner", "Check SAP Health"]

        try:
            from app.agent.react_agent import SYSTEM_PROMPT
            rag_reply = await nvidia_chat_service.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=f"The user said: '{message}'. Respond directly, conversationally, and helpfully in markdown tailored specifically to their input."
            )
            return {
                "success": True,
                "reply": rag_reply,
                "action": "EXPLAIN",
                "suggestions": dyn_suggestions
            }
        except Exception as e:
            logger.warning(f"Error in fallback: {e}")
            fallback_text = nvidia_chat_service._deterministic_fallback_response(message, "")
            return {
                "success": True,
                "reply": fallback_text,
                "action": "EXPLAIN",
                "suggestions": dyn_suggestions
            }


agent_service = AgentService()
