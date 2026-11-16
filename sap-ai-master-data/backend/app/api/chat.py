"""
Conversational Master Data Collection API.
Assists users in supplying missing mandatory fields and answers SAP technical questions.
"""
import re
from typing import Any, Dict, Optional
from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.models.extraction import MasterDataType
from app.models.workflow import WorkflowStatus
from app.rag.generator import rag_generator
from app.rag.prompts import CHAT_COLLECTION_PROMPT, STRICT_SAP_SYSTEM_PROMPT
from app.services.audit_service import AuditService
from app.services.chat_service import nvidia_chat_service
from app.services.normalization_service import normalization_service
from app.services.validation_service import validation_service

router = APIRouter(prefix="/api", tags=["Chat & Missing Fields"])

def is_inquiry(msg: str) -> bool:
    """Determine whether user input is an informational inquiry or question rather than field data."""
    m = msg.strip().lower()
    if m.endswith("?"):
        return True
    starters = ("what", "why", "how", "where", "who", "when", "can you", "could you", "tell me", "explain", "help", "show me")
    if any(m.startswith(w) for w in starters):
        if ":" not in msg:
            return True
    return False

def extract_field_value_from_reply(user_msg: str, missing_field: str) -> Optional[Any]:
    """Extract candidate value from user input for a specific missing field."""
    msg = user_msg.strip()
    
    # Common patterns: "Field is Value", "My field: Value", "Value"
    # If user used a colon: e.g. "ItemCode: ITM-001" or "Code: ITM-001"
    if ":" in msg:
        parts = msg.split(":", 1)
        return parts[1].strip()
    
    # If user used "is": e.g. "The ItemCode is ITM-001"
    if " is " in msg and not msg.lower().startswith(("what is", "where is", "why is", "how is")):
        parts = msg.split(" is ", 1)
        return parts[1].strip()
    
    return msg

@router.post("/chat")
@router.post("/chat/message")
async def chat_assistant(req: ChatRequest):
    """
    Handle user conversational messages:
    - If workflow_id is provided, process missing fields and update master data.
    - If user asks a question while missing fields exist, answer the question and remind of the missing field.
    - Re-run deterministic validation.
    - If user asks general SAP questions, route to RAG answering with citations.
    """
    user_msg = req.message.strip()
    workflow_id = req.workflow_id
    extracted_updates: Dict[str, Any] = {}
    citations = []

    if workflow_id:
        state = AuditService.get_workflow(workflow_id)
        if state:
            current_data = dict(state.normalized_data)
            missing = state.missing_fields

            # If there are missing fields, check if user is asking a question vs providing a value
            if missing:
                target_field_info = None
                user_msg_lower = user_msg.lower()

                # Check if user mentioned any of the missing fields specifically
                for m in missing:
                    m_field = (m.field if hasattr(m, "field") else str(m.get("field", ""))).lower()
                    m_label = (m.label if hasattr(m, "label") else str(m.get("label", ""))).lower()
                    if m_field in user_msg_lower or m_label in user_msg_lower:
                        target_field_info = m
                        break

                if not target_field_info:
                    target_field_info = missing[0]

                target_field = target_field_info.field if hasattr(target_field_info, "field") else target_field_info.get("field")
                target_label = target_field_info.label if hasattr(target_field_info, "label") else target_field_info.get("label", target_field)

                # If user asked a question rather than supplying data, answer via RAG and guide them
                if is_inquiry(user_msg):
                    try:
                        rag_res = await rag_generator.ask(user_msg)
                        base_reply = rag_res.get("answer", "")
                        citations = rag_res.get("sources", [])
                    except Exception:
                        base_reply = f"In SAP , **{target_label}** is a required master data field."
                        citations = []

                    reply = f"{base_reply}\n\n*(Note: For this record, **{target_label}** is required. When ready, please enter the value below.)*"
                    res_data = {
                        "reply": reply,
                        "workflow_id": workflow_id,
                        "extracted_updates": {},
                        "missing_fields": [m.model_dump() if hasattr(m, "model_dump") else m for m in missing],
                        "validation_status": "MISSING_FIELDS",
                        "citations": citations
                    }
                    return {
                        "success": True,
                        "status": "MISSING_FIELDS",
                        "message": reply,
                        "data": res_data,
                        **res_data
                    }

                # Otherwise user provided a candidate value
                provided_val = extract_field_value_from_reply(user_msg, target_field)
                if provided_val:
                    provided_val = normalization_service.normalize_field_value(target_field, provided_val)
                    extracted_updates[target_field] = provided_val
                    current_data[target_field] = provided_val
                    state.user_corrections[target_field] = provided_val

                    # If GSTNo was provided as a 15-char GSTIN and PANNo was missing, auto-populate PANNo
                    if target_field == "GSTNo" and isinstance(provided_val, str) and len(provided_val) == 15 and provided_val[:2].isdigit():
                        if not current_data.get("PANNo"):
                            pan_val = provided_val[2:12]
                            current_data["PANNo"] = pan_val
                            extracted_updates["PANNo"] = pan_val

                    state.normalized_data = current_data

                    # If extracted_records exists (e.g. bulk CSV/Excel), update the record there as well
                    if state.extracted_records:
                        for rec in state.extracted_records:
                            if rec.get("CardCode") == current_data.get("CardCode") or rec.get("ItemCode") == current_data.get("ItemCode"):
                                rec[target_field] = provided_val

                    # Re-run deterministic validation
                    val_result = validation_service.validate(state.master_type, current_data)
                    state.validation_result = val_result
                    state.missing_fields = val_result.missing_fields

                    if val_result.valid:
                        state.status = WorkflowStatus.READY_FOR_CONFIRMATION
                        state.final_payload = val_result.validated_data
                        state.message = "All required fields are complete and validated. Ready for confirmation."
                        AuditService.save_workflow(state)

                        reply = (
                            f"Thank you! I have recorded **{target_label}** as `{provided_val}`. "
                            "All required fields for this master data record are now complete and validated! "
                            "You can now review the preview table and click **Confirm & Create in SAP**."
                        )
                        res_data = {
                            "reply": reply,
                            "workflow_id": workflow_id,
                            "extracted_updates": extracted_updates,
                            "missing_fields": [],
                            "validation_status": "READY_FOR_CONFIRMATION",
                            "citations": []
                        }
                        return {
                            "success": True,
                            "status": "READY_FOR_CONFIRMATION",
                            "message": reply,
                            "data": res_data,
                            **res_data
                        }
                    else:
                        AuditService.save_workflow(state)
                        if val_result.missing_fields:
                            next_missing = val_result.missing_fields[0]
                            next_label = next_missing.label if hasattr(next_missing, "label") else next_missing.get("label")
                            next_reason = next_missing.reason if hasattr(next_missing, "reason") else next_missing.get("reason", "")
                            reply = (
                                f"Thank you! Recorded **{target_label}** as `{provided_val}`. "
                                f"Next, please provide the **{next_label}** ({next_reason})."
                            )
                            val_status = "MISSING_FIELDS"
                        else:
                            invalid_descs = [f"{err.field}: {err.message}" for err in val_result.invalid_fields]
                            err_text = "; ".join(invalid_descs) if invalid_descs else "Validation rules failed."
                            reply = (
                                f"Thank you! Recorded **{target_label}** as `{provided_val}`, but validation issues were found: {err_text}."
                            )
                            val_status = "VALIDATION_FAILED"

                        res_data = {
                            "reply": reply,
                            "workflow_id": workflow_id,
                            "extracted_updates": extracted_updates,
                            "missing_fields": [m.model_dump() if hasattr(m, "model_dump") else m for m in val_result.missing_fields],
                            "validation_status": val_status,
                            "citations": []
                        }
                        return {
                            "success": True,
                            "status": val_status,
                            "message": reply,
                            "data": res_data,
                            **res_data
                        }
                else:
                    reply = f"Please provide a valid value for **{target_label}**."
                    res_data = {
                        "reply": reply,
                        "workflow_id": workflow_id,
                        "extracted_updates": {},
                        "missing_fields": [m.model_dump() if hasattr(m, "model_dump") else m for m in missing],
                        "validation_status": "MISSING_FIELDS",
                        "citations": []
                    }
                    return {
                        "success": True,
                        "status": "MISSING_FIELDS",
                        "message": reply,
                        "data": res_data,
                        **res_data
                    }

    # General technical question or general conversational query -> RAG routing
    try:
        rag_res = await rag_generator.ask(user_msg)
        reply = rag_res.get("answer", "")
        citations = rag_res.get("sources", [])
    except Exception as e:
        reply = (
            "I am your SAP technical assistant. "
            "Please upload your master data document or provide missing fields to proceed."
        )
        citations = []

    res_data = {
        "reply": reply,
        "workflow_id": workflow_id,
        "extracted_updates": {},
        "missing_fields": [],
        "validation_status": "COMPLETE" if workflow_id else None,
        "citations": citations
    }
    return {
        "success": True,
        "status": "SUCCESS",
        "message": "Assistant answer generated.",
        "data": res_data,
        **res_data
    }
