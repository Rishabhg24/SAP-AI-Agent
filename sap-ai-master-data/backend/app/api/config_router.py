"""
Dynamic Configuration and Connections API endpoints.
Provides safe, authorized access to read and update connections.json at runtime without hardcoding.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import get_safe_connections_export, save_connections_dict, reload_settings
from app.utils.logging import logger

router = APIRouter(prefix="/api/config", tags=["Dynamic Configuration"])

class UpdateConnectionsRequest(BaseModel):
    server: Optional[Dict[str, Any]] = None
    sap: Optional[Dict[str, Any]] = None
    ai: Optional[Dict[str, Any]] = None
    database: Optional[Dict[str, Any]] = None

@router.get("/connections")
async def get_connections():
    """
    Returns the current connection parameters with credentials masked.
    Enables UI and integrations to inspect active configuration dynamically.
    """
    data = get_safe_connections_export()
    return {
        "success": True,
        "status": "SUCCESS",
        "message": "Dynamic connection configuration retrieved.",
        "data": data
    }

@router.post("/connections")
async def update_connections(payload: Dict[str, Any]):
    """
    Updates connections.json and reloads settings dynamically in-memory.
    Allows changing webserver host/port, SAP Service Layer credentials, and AI parameters
    without restarting the server or editing source code.
    """
    success, msg = save_connections_dict(payload)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    data = get_safe_connections_export()
    return {
        "success": True,
        "status": "SUCCESS",
        "message": msg,
        "data": data
    }

@router.post("/reload")
async def reload_configuration():
    """
    Reloads connections.json directly from disk and refreshes in-memory settings.
    """
    try:
        reload_settings()
        data = get_safe_connections_export()
        return {
            "success": True,
            "status": "SUCCESS",
            "message": "Configuration reloaded from disk successfully.",
            "data": data
        }
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))
