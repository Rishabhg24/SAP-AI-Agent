"""
Deterministic validation endpoints for Item, Business Partner, and Warehouse master data.
"""
from typing import Any, Dict
from fastapi import APIRouter
from app.models.extraction import MasterDataType
from app.services.validation_service import validation_service

router = APIRouter(prefix="/api/validation", tags=["Deterministic Validation"])

@router.post("/item")
async def validate_item_data(payload: Dict[str, Any]):
    """Deterministically validate Item Master properties against SAP schema."""
    res = validation_service.validate_item(payload)
    return {
        "success": res.valid,
        "status": "VALID" if res.valid else "INVALID",
        "message": "Item validation passed." if res.valid else "Validation errors or missing mandatory fields detected.",
        "data": res.model_dump()
    }

@router.post("/business-partner")
async def validate_bp_data(payload: Dict[str, Any]):
    """Deterministically validate Business Partner properties against SAP schema."""
    res = validation_service.validate_business_partner(payload)
    return {
        "success": res.valid,
        "status": "VALID" if res.valid else "INVALID",
        "message": "Business Partner validation passed." if res.valid else "Validation errors or missing mandatory fields detected.",
        "data": res.model_dump()
    }

@router.post("/warehouse")
async def validate_warehouse_data(payload: Dict[str, Any]):
    """Deterministically validate Warehouse properties against SAP schema."""
    res = validation_service.validate_warehouse(payload)
    return {
        "success": res.valid,
        "status": "VALID" if res.valid else "INVALID",
        "message": "Warehouse validation passed." if res.valid else "Validation errors or missing mandatory fields detected.",
        "data": res.model_dump()
    }
