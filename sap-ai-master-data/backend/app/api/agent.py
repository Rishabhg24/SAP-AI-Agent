"""
Autonomous SAP AI Agent API Router.
Provides conversational AI endpoints, direct field update actions, and 1-click master data creation confirmation.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel, Field

from app.services.agent_service import agent_service
from app.utils.logging import logger

router = APIRouter(prefix="/api/agent", tags=["Autonomous SAP AI Agent"])


class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Natural language command or question for the AI Agent")
    history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous conversational dialogue turns")


class DirectFieldUpdateRequest(BaseModel):
    entity: str = Field(..., description="SAP Entity: BusinessPartners, Items, or Warehouses")
    key: str = Field(..., description="Target record code (e.g. CardCode, ItemCode, WarehouseCode)")
    fields: Dict[str, Any] = Field(..., description="Key-value dictionary of SAP fields to update")


class AgentConfirmCreateRequest(BaseModel):
    entity: str = Field(..., description="SAP Entity: BusinessPartners, Items, or Warehouses")
    data: Dict[str, Any] = Field(..., description="Complete creation payload")


@router.post("/chat")
async def agent_chat_endpoint(req: AgentChatRequest):
    """
    Autonomous AI Agent dialogue endpoint.
    Understands interactive multi-turn master data creation, granular attribute queries, field updates, and table querying.
    """
    try:
        result = await agent_service.process_chat(message=req.message, history=req.history)
        return {
            "success": result.get("success", True),
            "status": "SUCCESS" if result.get("success", True) else "FAILED",
            "reply": result.get("reply", ""),
            "action": result.get("action", "EXPLAIN"),
            "entity": result.get("entity"),
            "records": result.get("records", []),
            "total": result.get("total", len(result.get("records", []))),
            "update_result": result.get("update_result"),
            "creation_draft": result.get("creation_draft"),
            "missing_fields": result.get("missing_fields", []),
            "is_creation_ready": result.get("is_creation_ready", False),
            "granular_answer": result.get("granular_answer"),
            "suggestions": result.get("suggestions", []),
            "prompt": req.message,
            "query_type": result.get("query_type"),
            "filters": result.get("filters"),
            "sources": result.get("sources", [])
        }
    except Exception as e:
        logger.error(f"Error in agent chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm-create")
async def agent_confirm_create_endpoint(req: AgentConfirmCreateRequest):
    """
    Executes 1-click master data creation into SAP Business One Service Layer
    from an agent interactive draft card.
    """
    if req.entity not in ["BusinessPartners", "Items", "Warehouses"]:
        raise HTTPException(status_code=400, detail=f"Entity '{req.entity}' is not allowlisted.")

    try:
        result = await agent_service.execute_create_master_data(
            entity=req.entity,
            data=req.data
        )
        return {
            "success": result.get("success", True),
            "status": "SUCCESS" if result.get("success", True) else "FAILED",
            "reply": result.get("reply", ""),
            "action": result.get("action", "CREATE_SUCCESS"),
            "entity": req.entity,
            "records": result.get("records", []),
            "total": 1,
            "creation_draft": result.get("creation_draft"),
            "is_creation_ready": True,
            "suggestions": result.get("suggestions", [])
        }
    except Exception as e:
        logger.error(f"Error in agent confirm create endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-field")
async def direct_field_update_endpoint(req: DirectFieldUpdateRequest):
    """
    Direct helper endpoint for updating single or multiple fields on allowlisted SAP entities.
    Invoked directly by interactive workspace table quick-edit actions.
    """
    if req.entity not in ["BusinessPartners", "Items", "Warehouses"]:
        raise HTTPException(status_code=400, detail=f"Entity '{req.entity}' is not allowlisted.")

    try:
        prompt_desc = f"Direct field update for {req.entity}('{req.key}')"
        result = await agent_service.execute_field_update(
            entity=req.entity,
            key=req.key,
            fields=req.fields,
            prompt=prompt_desc
        )
        return {
            "success": result.get("success", True),
            "status": "SUCCESS" if result.get("success", True) else "FAILED",
            "reply": result.get("reply", ""),
            "action": "UPDATE",
            "entity": req.entity,
            "records": result.get("records", []),
            "update_result": result.get("update_result"),
            "suggestions": result.get("suggestions", [])
        }
    except Exception as e:
        logger.error(f"Error in direct field update endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_agent_suggestions():
    """Get context-aware suggested prompt chips for the executive copilot."""
    return {
        "success": True,
        "suggestions": [
            {"label": "Create a Business Partner", "icon": "plus", "category": "create"},
            {"label": "Add new Item Master", "icon": "package-plus", "category": "create"},
            {"label": "What is the address of customer C20000?", "icon": "map-pin", "category": "granular"},
            {"label": "List all Business Partners", "icon": "building", "category": "query"},
            {"label": "List all Warehouses", "icon": "warehouse", "category": "query"},
            {"label": "List all Items", "icon": "package", "category": "query"},
            {"label": "Check SAP Health", "icon": "zap", "category": "health"}
        ]
    }


class SaveSessionRequest(BaseModel):
    session_id: str
    title: Optional[str] = "AI Copilot Session"
    user_id: Optional[str] = "cinntra_user"
    company_db: Optional[str] = "CINNTRA_DEMO_NEW"
    messages: List[Dict[str, Any]]


@router.get("/history")
async def get_agent_history_endpoint(
    limit: int = 50,
    offset: int = 0,
    days: Optional[int] = None,
    entity: Optional[str] = None,
    action: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    company_db: Optional[str] = None
):
    """
    Query chronological audit log history of all changes and operations performed by the AI Agent.
    Includes visual old vs new value diffs, payload hashes, and execution timestamps.
    """
    try:
        from app.services.audit_service import AuditService
        result = AuditService.get_agent_history(
            limit=limit,
            offset=offset,
            days=days,
            entity=entity,
            action=action,
            search=search,
            user_id=user_id,
            company_db=company_db
        )
        return {
            "success": True,
            "status": "SUCCESS",
            **result
        }
    except Exception as e:
        logger.error(f"Error fetching agent history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/stats")
async def get_agent_history_stats_endpoint(company_db: Optional[str] = None):
    """Get aggregated KPI metrics for AI Agent activities."""
    try:
        from app.services.audit_service import AuditService
        stats = AuditService.get_agent_history_stats(company_db=company_db)
        return {
            "success": True,
            "status": "SUCCESS",
            **stats
        }
    except Exception as e:
        logger.error(f"Error fetching agent history stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions")
async def save_agent_session_endpoint(req: SaveSessionRequest):
    """Persist conversation session state across browser reloads."""
    try:
        from app.services.audit_service import AuditService
        saved = AuditService.save_agent_chat_session(
            session_id=req.session_id,
            title=req.title or "AI Copilot Session",
            user_id=req.user_id or "cinntra_user",
            company_db=req.company_db or "CINNTRA_DEMO_NEW",
            messages=req.messages
        )
        return {
            "success": True,
            "status": "SUCCESS",
            "data": saved
        }
    except Exception as e:
        logger.error(f"Error saving agent chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_agent_sessions_endpoint(user_id: Optional[str] = None, limit: int = 20):
    """List saved conversation sessions."""
    try:
        from app.services.audit_service import AuditService
        sessions = AuditService.list_agent_chat_sessions(user_id=user_id, limit=limit)
        return {
            "success": True,
            "status": "SUCCESS",
            "sessions": sessions
        }
    except Exception as e:
        logger.error(f"Error listing agent sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_agent_session_endpoint(session_id: str):
    """Retrieve full messages for a specific conversation session."""
    try:
        from app.services.audit_service import AuditService
        session = AuditService.get_agent_chat_session(session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {
            "success": True,
            "status": "SUCCESS",
            "session": session
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agent session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_agent_session_endpoint(session_id: str):
    """Delete a saved conversation session."""
    try:
        from app.services.audit_service import AuditService
        deleted = AuditService.delete_agent_chat_session(session_id=session_id)
        return {
            "success": deleted,
            "status": "SUCCESS" if deleted else "NOT_FOUND"
        }
    except Exception as e:
        logger.error(f"Error deleting agent session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    language: Optional[str] = "en"
):
    """
    Transcribe audio recording for AI Agent commands.
    Accepts recorded audio blob (webm/wav/mp4/ogg) and returns transcribed text.
    Uses OpenAI/NVIDIA Whisper if configured, or returns transcription status.
    """
    import os
    import tempfile

    try:
        content = await audio.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio recording received.")

        # Save temporarily for transcription processing
        suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                with open(tmp_path, "rb") as f:
                    transcript_obj = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f,
                        language=language[:2] if language and len(language) >= 2 else None
                    )
                return {
                    "success": True,
                    "text": transcript_obj.text,
                    "language": language
                }
            else:
                return {
                    "success": True,
                    "text": "",
                    "message": "Audio received. Web Speech Recognition active on client."
                }
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Audio transcription error: {e}")
        return {
            "success": False,
            "text": "",
            "message": str(e)
        }


