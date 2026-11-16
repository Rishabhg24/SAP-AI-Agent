"""
SAP Service Layer connectivity, counts, company database selection, and live records endpoints.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from app.config import settings, get_available_companies, set_active_company_db
from app.sap.client import sap_client
from app.services.audit_service import AuditService
from app.models.workflow import AuditLogRecord

router = APIRouter(prefix="/api/sap", tags=["SAP Service Layer Connectivity"])

class SelectCompanyRequest(BaseModel):
    company_db: str
    user_id: Optional[str] = "cinntra_user"

@router.get("/health")
async def get_sap_health():
    """
    Check connectivity to SAP Business One Service Layer safely.
    Never exposes passwords, session tokens, or internal secrets.
    """
    health = await sap_client.check_health()
    is_connected = bool(health.get("connected", False))
    available_comps = get_available_companies()
    active_company_info = next((c for c in available_comps if c.get("is_active")), None)
    return {
        "connected": is_connected,
        "success": is_connected,
        "status": health.get("status", "CONNECTED" if is_connected else "NOT_CONNECTED"),
        "message": health.get("message", ""),
        "service_layer_url": health.get("service_layer_url", settings.sap_service_layer_url or ""),
        "username": health.get("username", settings.sap_username or ""),
        "company_name": active_company_info.get("company_name", settings.sap_company_db) if active_company_info else settings.sap_company_db,
        "company_db": settings.sap_company_db,
        "available_companies": available_comps,
        "data": health
    }

@router.get("/companies")
async def list_companies():
    """
    Retrieve all available SAP Business One databases/companies with active flag.
    """
    comps = get_available_companies()
    active_comp = next((c for c in comps if c.get("is_active")), None)
    return {
        "success": True,
        "status": "SUCCESS",
        "active_company_db": settings.sap_company_db,
        "active_company_name": active_comp.get("company_name", settings.sap_company_db) if active_comp else settings.sap_company_db,
        "companies": comps
    }

@router.post("/select-company")
async def select_company(req: SelectCompanyRequest, x_user_id: Optional[str] = Header(None)):
    """
    Dynamically switches the active SAP Business One company database before performing transactions.
    Logs the company switch event for administrative auditing.
    """
    prev_db = settings.sap_company_db
    target_db = req.company_db.strip()
    user_id = x_user_id or req.user_id or "cinntra_user"

    if not target_db:
        raise HTTPException(status_code=400, detail="Company database name is required.")

    ok, msg = set_active_company_db(target_db)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Invalidate and re-check health for the newly selected company database
    health = await sap_client.check_health()
    available_comps = get_available_companies()
    active_comp = next((c for c in available_comps if c.get("is_active")), None)
    company_name = active_comp.get("company_name", target_db) if active_comp else target_db

    # Record audit log for database switch
    AuditService.record_audit(AuditLogRecord(
        workflow_id="system_config",
        master_type="system",
        action="DATABASE_SWITCH",
        activity="SELECT_COMPANY_DATABASE",
        user_id=user_id,
        user_identifier=user_id,
        company_db=target_db,
        transaction_num=f"SWITCH_{target_db}",
        previous_value=prev_db,
        updated_value=target_db,
        success=True,
        details=f"User '{user_id}' switched active SAP Company database from '{prev_db}' to '{target_db}' ({company_name})"
    ))

    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Switched active SAP Company to '{company_name}' ({target_db}) successfully.",
        "active_company_db": target_db,
        "active_company_name": company_name,
        "health": health
    }

@router.get("/counts")
async def get_sap_counts():
    """Retrieve total record counts directly from SAP Business One database."""
    counts = await sap_client.get_entity_counts()
    return {
        "success": True,
        "status": "SUCCESS",
        "company_db": settings.sap_company_db,
        "data": counts
    }

@router.get("/records")
async def get_sap_records(
    entity: str = Query(default="Items", description="SAP Entity: Items, BusinessPartners, or Warehouses"),
    top: int = Query(default=15, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Filter records by last N days")
):
    """Retrieve real master data records directly from SAP Business One Service Layer with optional days filter."""
    if entity not in ["Items", "BusinessPartners", "Warehouses"]:
        raise HTTPException(status_code=400, detail=f"Entity '{entity}' not in allowlist.")
    result = await sap_client.get_live_records(entity=entity, top=top, skip=skip, search=search, days=days)
    return {
        "success": "error" not in result,
        "status": "SUCCESS" if "error" not in result else "ERROR",
        "company_db": settings.sap_company_db,
        "data": result
    }


