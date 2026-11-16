import asyncio
import csv
from datetime import datetime
import io
import json
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field
from app.models.business_partner import BusinessPartnerCreate
from app.models.extraction import MasterDataType
from app.models.item import ItemMasterCreate
from app.models.warehouse import WarehouseCreate
from app.models.workflow import AuditLogRecord, BulkCreationSummary, BulkRecordResult, WorkflowStatus
from app.sap.business_partners import SAPBusinessPartnersService
from app.sap.items import SAPItemsService
from app.sap.warehouses import SAPWarehousesService
from app.services.audit_service import AuditService
from app.services.duplicate_service import duplicate_service
from app.services.validation_service import validation_service
from app.config import settings
from app.sap.client import sap_client
from app.utils.logging import logger
from app.utils.security import hash_payload

router = APIRouter(prefix="/api", tags=["Master Data Creation & Audit"])

class ConfirmationRequest(BaseModel):
    confirmed: bool

class MasterDataCreationRequest(BaseModel):
    workflow_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class BulkCreationRequest(BaseModel):
    indices: Optional[List[int]] = None
    skip_duplicates: bool = True
    continue_on_error: bool = True
    confirmed: Optional[bool] = None

class DirectBulkCreationRequest(BaseModel):
    master_type: Optional[str] = "item"
    records: List[Dict[str, Any]]
    skip_duplicates: bool = True
    continue_on_error: bool = True
    confirmed: bool = True

@router.post("/master-data/{workflow_id}/confirm")
async def confirm_workflow(workflow_id: str, req: ConfirmationRequest):
    """
    Explicit user confirmation gate.
    Requires user to explicitly click 'Confirm & Create in SAP'.
    Verifies:
    1. Workflow exists
    2. Extraction succeeded without unresolved conflicts
    3. Mandatory fields present and deterministic validation passed
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not req.confirmed:
        state.status = WorkflowStatus.CANCELLED
        state.message = "Master data creation was cancelled by the user."
        AuditService.save_workflow(state)
        return {
            "success": True,
            "status": state.status.value,
            "message": state.message,
            "data": {"workflow_id": workflow_id, "is_confirmed": False}
        }

    # Verify no unresolved conflicts
    if state.status == WorkflowStatus.EXTRACTION_CONFLICT:
        return {
            "success": False,
            "status": "CONFLICT_UNRESOLVED",
            "message": "Cannot confirm master data: unresolved extraction conflicts exist. Please resolve them first.",
            "errors": ["Unresolved extraction conflicts"]
        }

    # Deterministic validation and enrichment
    val_res = validation_service.validate(state.master_type, state.normalized_data)
    state.is_confirmed = True
    state.status = WorkflowStatus.CONFIRMED
    state.final_payload = val_res.validated_data or state.normalized_data
    state.message = "Master data confirmed. Ready for direct SAP creation."
    AuditService.save_workflow(state)

    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": {
            "workflow_id": workflow_id,
            "is_confirmed": True,
            "master_type": state.master_type.value,
            "payload": state.final_payload
        }
    }

@router.post("/master-data/{workflow_id}/bulk-confirm")
async def bulk_confirm_workflow(workflow_id: str, req: ConfirmationRequest):
    """
    Explicit user confirmation gate for bulk execution.
    Requires user to explicitly confirm before posting batch records to SAP.
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not req.confirmed:
        state.status = WorkflowStatus.CANCELLED
        state.message = "Bulk creation was cancelled by the user."
        AuditService.save_workflow(state)
        return {
            "success": True,
            "status": state.status.value,
            "message": state.message,
            "data": {"workflow_id": workflow_id, "is_confirmed": False}
        }

    if state.status == WorkflowStatus.EXTRACTION_CONFLICT:
        return {
            "success": False,
            "status": "CONFLICT_UNRESOLVED",
            "message": "Cannot confirm master data: unresolved extraction conflicts exist.",
            "errors": ["Unresolved extraction conflicts"]
        }

    state.is_confirmed = True
    state.status = WorkflowStatus.CONFIRMED
    state.message = "Bulk master data explicitly confirmed by user. Ready for SAP creation."
    AuditService.save_workflow(state)

    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": {
            "workflow_id": workflow_id,
            "is_confirmed": True,
            "master_type": state.master_type.value
        }
    }

@router.post("/master-data/{workflow_id}/bulk-create")
async def bulk_create_in_sap(workflow_id: str, req: BulkCreationRequest):
    """
    Bulk create master data records in SAP Business One via Service Layer.
    Executes concurrent, safe posting with semaphore control (limit: 4).
    Enforces deterministic validation, duplicate checking, and audit logging per record.
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if req.confirmed:
        state.is_confirmed = True

    if not state.is_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Security Gate: Explicit user confirmation is required before posting batch records to SAP."
        )

    all_records = list(state.extracted_records or [state.normalized_data])
    if not all_records:
        raise HTTPException(status_code=400, detail="No extracted records found in workflow.")

    if req.indices is not None and len(req.indices) > 0:
        target_indices = [i for i in req.indices if 0 <= i < len(all_records)]
    else:
        target_indices = list(range(len(all_records)))

    if not target_indices:
        raise HTTPException(status_code=400, detail="No valid records selected for bulk creation.")

    state.status = WorkflowStatus.CREATING_IN_SAP
    state.message = f"Creating {len(target_indices)} records in SAP..."
    AuditService.save_workflow(state)

    sem = asyncio.Semaphore(4)

    async def process_record(idx: int) -> BulkRecordResult:
        rec = all_records[idx]
        start_time = time.time()

        if state.master_type == MasterDataType.ITEM:
            code = str(rec.get("ItemCode") or f"Row-{idx + 1}").strip().upper()
            name = str(rec.get("ItemName") or "")
        elif state.master_type == MasterDataType.BUSINESS_PARTNER:
            code = str(rec.get("CardCode") or f"Row-{idx + 1}").strip().upper()
            name = str(rec.get("CardName") or "")
        else:
            code = str(rec.get("WarehouseCode") or f"Row-{idx + 1}").strip().upper()
            name = str(rec.get("WarehouseName") or "")

        # 1. Deterministic Enrichment with minimal defaults
        val_res = validation_service.validate(state.master_type, rec)
        valid_data = val_res.validated_data or dict(rec)

        if state.master_type == MasterDataType.ITEM:
            code = str(valid_data.get("ItemCode") or f"ITM{idx + 1}").strip()
            name = str(valid_data.get("ItemName") or f"Item {code}").strip()
        elif state.master_type == MasterDataType.BUSINESS_PARTNER:
            code = str(valid_data.get("CardCode") or f"V{idx + 1}").strip()[:15]
            name = str(valid_data.get("CardName") or f"BP {code}").strip()
        else:
            code = str(valid_data.get("WarehouseCode") or f"W{idx + 1}").strip()[:8]
            name = str(valid_data.get("WarehouseName") or f"Warehouse {code}").strip()

        # 2. Duplicate Check
        async with sem:
            is_dup, dup_msg = await duplicate_service.check_duplicate(state.master_type, valid_data)
            if is_dup:
                return BulkRecordResult(
                    index=idx,
                    code=code,
                    name=name,
                    status="DUPLICATE",
                    error=dup_msg or "Already exists in SAP (Skipped)",
                    duration_ms=round((time.time() - start_time) * 1000, 2)
                )

            # 3. Create Model & Service Layer Payload
            try:
                if state.master_type == MasterDataType.ITEM:
                    model = ItemMasterCreate(**valid_data)
                    payload = model.to_service_layer_payload()
                    payload_hash = hash_payload(payload)
                    sap_res = await SAPItemsService.create_item(model)
                    sap_obj_id = sap_res.get("ItemCode", model.ItemCode)
                elif state.master_type == MasterDataType.BUSINESS_PARTNER:
                    model = BusinessPartnerCreate(**valid_data)
                    payload = model.to_service_layer_payload()
                    payload_hash = hash_payload(payload)
                    sap_res = await SAPBusinessPartnersService.create_business_partner(model)
                    sap_obj_id = sap_res.get("CardCode", model.CardCode)
                else:
                    model = WarehouseCreate(**valid_data)
                    payload = model.to_service_layer_payload()
                    payload_hash = hash_payload(payload)
                    sap_res = await SAPWarehousesService.create_warehouse(model)
                    sap_obj_id = sap_res.get("WarehouseCode", model.WarehouseCode)

                AuditService.record_audit(AuditLogRecord(
                    workflow_id=workflow_id,
                    master_type=state.master_type.value,
                    action="CREATE",
                    payload_hash=payload_hash,
                    sap_response_status=201,
                    sap_object_id=sap_obj_id,
                    success=True,
                    details=f"Bulk created in SAP Service Layer: {sap_obj_id}"
                ))

                return BulkRecordResult(
                    index=idx,
                    code=code,
                    name=name,
                    status="CREATED",
                    sap_object_id=sap_obj_id,
                    duration_ms=round((time.time() - start_time) * 1000, 2)
                )
            except Exception as ex:
                err_str = str(ex)
                AuditService.record_audit(AuditLogRecord(
                    workflow_id=workflow_id,
                    master_type=state.master_type.value,
                    action="CREATE",
                    payload_hash=hash_payload(valid_data),
                    sap_response_status=500,
                    sap_object_id=None,
                    success=False,
                    details=f"Failed to bulk create {code}: {err_str}"
                ))
                return BulkRecordResult(
                    index=idx,
                    code=code,
                    name=name,
                    status="SAP_ERROR",
                    error=err_str,
                    duration_ms=round((time.time() - start_time) * 1000, 2)
                )

    tasks = [process_record(idx) for idx in target_indices]
    results = await asyncio.gather(*tasks)

    created = sum(1 for r in results if r.status == "CREATED")
    duplicates = sum(1 for r in results if r.status == "DUPLICATE")
    failed = sum(1 for r in results if r.status in ["VALIDATION_ERROR", "SAP_ERROR"])

    summary = BulkCreationSummary(
        total_submitted=len(target_indices),
        created_count=created,
        duplicate_count=duplicates,
        failed_count=failed,
        records=list(results),
        completed_at=datetime.utcnow().isoformat()
    )

    state.bulk_results = summary
    if failed == 0:
        state.status = WorkflowStatus.CREATED
        state.message = f"Successfully created all {created} records in SAP."
    elif created > 0:
        state.status = WorkflowStatus.CREATED
        state.message = f"Bulk creation finished: {created} created, {duplicates} duplicates, {failed} failed."
    else:
        state.status = WorkflowStatus.SAP_ERROR
        state.message = f"Bulk creation failed: {failed} errors encountered."

    AuditService.save_workflow(state)

    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": {
            "workflow_id": workflow_id,
            "master_type": state.master_type.value,
            "summary": summary.model_dump()
        }
    }

@router.post("/master-data/bulk-create-direct")
@router.post("/master-data/{master_type}/bulk-create-direct")
async def bulk_create_direct(req: DirectBulkCreationRequest, master_type: Optional[str] = None):
    """
    Direct bulk creation of master data records in SAP Business One.
    Accepts raw list of records, performs deterministic validation, duplicate checking,
    concurrent posting via Semaphore(4), audit logging, and returns BulkCreationSummary.
    """
    m_type_str = (master_type or req.master_type or "item").lower()
    try:
        m_type = MasterDataType(m_type_str)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid master data type: '{m_type_str}'")

    if not req.records:
        raise HTTPException(status_code=400, detail="No records provided for bulk creation.")

    if not req.confirmed:
        raise HTTPException(status_code=400, detail="Security Gate: Explicit user confirmation required.")

    sem = asyncio.Semaphore(4)

    async def process_direct_record(idx: int, rec: Dict[str, Any]) -> BulkRecordResult:
        start_time = time.time()
        if m_type == MasterDataType.ITEM:
            code = str(rec.get("ItemCode") or f"Row-{idx + 1}").strip().upper()
            name = str(rec.get("ItemName") or "")
        elif m_type == MasterDataType.BUSINESS_PARTNER:
            code = str(rec.get("CardCode") or f"Row-{idx + 1}").strip().upper()
            name = str(rec.get("CardName") or "")
        else:
            code = str(rec.get("WarehouseCode") or f"Row-{idx + 1}").strip().upper()
            name = str(rec.get("WarehouseName") or "")

        # 1. Deterministic Enrichment with minimal defaults
        val_res = validation_service.validate(m_type, rec)
        valid_data = val_res.validated_data or dict(rec)

        if m_type == MasterDataType.ITEM:
            code = str(valid_data.get("ItemCode") or f"ITM{idx + 1}").strip()
            name = str(valid_data.get("ItemName") or f"Item {code}").strip()
        elif m_type == MasterDataType.BUSINESS_PARTNER:
            code = str(valid_data.get("CardCode") or f"V{idx + 1}").strip()[:15]
            name = str(valid_data.get("CardName") or f"BP {code}").strip()
        else:
            code = str(valid_data.get("WarehouseCode") or f"W{idx + 1}").strip()[:8]
            name = str(valid_data.get("WarehouseName") or f"Warehouse {code}").strip()

        # 2. Duplicate Check
        async with sem:
            if req.skip_duplicates:
                is_dup, dup_msg = await duplicate_service.check_duplicate(m_type, valid_data)
                if is_dup:
                    return BulkRecordResult(
                        index=idx,
                        code=code,
                        name=name,
                        status="DUPLICATE",
                        error=dup_msg or "Already exists in SAP (Skipped)",
                        duration_ms=round((time.time() - start_time) * 1000, 2)
                    )

            # 3. Create Model & Service Layer Payload
            try:
                if m_type == MasterDataType.ITEM:
                    model = ItemMasterCreate(**valid_data)
                    payload = model.to_service_layer_payload()
                    payload_hash = hash_payload(payload)
                    sap_res = await SAPItemsService.create_item(model)
                    sap_obj_id = sap_res.get("ItemCode", model.ItemCode)
                elif m_type == MasterDataType.BUSINESS_PARTNER:
                    model = BusinessPartnerCreate(**valid_data)
                    payload = model.to_service_layer_payload()
                    payload_hash = hash_payload(payload)
                    sap_res = await SAPBusinessPartnersService.create_business_partner(model)
                    sap_obj_id = sap_res.get("CardCode", model.CardCode)
                else:
                    model = WarehouseCreate(**valid_data)
                    payload = model.to_service_layer_payload()
                    payload_hash = hash_payload(payload)
                    sap_res = await SAPWarehousesService.create_warehouse(model)
                    sap_obj_id = sap_res.get("WarehouseCode", model.WarehouseCode)

                AuditService.record_audit(AuditLogRecord(
                    workflow_id="direct_bulk",
                    master_type=m_type.value,
                    action="CREATE",
                    payload_hash=payload_hash,
                    sap_response_status=201,
                    sap_object_id=sap_obj_id,
                    success=True,
                    details=f"Direct bulk created in SAP: {sap_obj_id}"
                ))

                return BulkRecordResult(
                    index=idx,
                    code=code,
                    name=name,
                    status="CREATED",
                    sap_object_id=sap_obj_id,
                    duration_ms=round((time.time() - start_time) * 1000, 2)
                )
            except Exception as ex:
                err_str = str(ex)
                AuditService.record_audit(AuditLogRecord(
                    workflow_id="direct_bulk",
                    master_type=m_type.value,
                    action="CREATE",
                    payload_hash=hash_payload(valid_data),
                    sap_response_status=500,
                    sap_object_id=None,
                    success=False,
                    details=f"Direct bulk create failed for {code}: {err_str}"
                ))
                return BulkRecordResult(
                    index=idx,
                    code=code,
                    name=name,
                    status="SAP_ERROR",
                    error=err_str,
                    duration_ms=round((time.time() - start_time) * 1000, 2)
                )

    tasks = [process_direct_record(idx, rec) for idx, rec in enumerate(req.records)]
    results = await asyncio.gather(*tasks)

    created = sum(1 for r in results if r.status == "CREATED")
    duplicates = sum(1 for r in results if r.status == "DUPLICATE")
    failed = sum(1 for r in results if r.status in ["VALIDATION_ERROR", "SAP_ERROR"])

    summary = BulkCreationSummary(
        total_submitted=len(req.records),
        created_count=created,
        duplicate_count=duplicates,
        failed_count=failed,
        records=list(results),
        completed_at=datetime.utcnow().isoformat()
    )

    return {
        "success": True,
        "status": "SUCCESS" if failed == 0 else ("PARTIAL" if created > 0 else "FAILED"),
        "message": f"Direct bulk creation completed: {created} created, {duplicates} duplicates, {failed} failed.",
        "data": {
            "master_type": m_type.value,
            "summary": summary.model_dump()
        }
    }

@router.post("/master-data/item/create")
async def create_item_in_sap(req: MasterDataCreationRequest):
    """
    Create Item Master in SAP Business One via Service Layer (/b1s/v2/Items).
    Enforces confirmation gate, duplicate check, and audit logging.
    """
    state = None
    data = req.data

    if req.workflow_id:
        state = AuditService.get_workflow(req.workflow_id)
        if not state:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if not state.is_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Security Gate: Explicit user confirmation is required before posting to SAP."
            )
        data = state.final_payload or state.normalized_data

    if not data:
        raise HTTPException(status_code=400, detail="No item data provided for SAP creation.")

    # Step 11: Validate & enrich deterministically
    val_res = validation_service.validate_item(data)
    valid_data = val_res.validated_data or dict(data)
    item_model = ItemMasterCreate(**valid_data)

    # Step 15: Duplicate checking
    is_dup, dup_msg = await duplicate_service.check_duplicate(MasterDataType.ITEM, data)
    if is_dup:
        if state:
            state.status = WorkflowStatus.DUPLICATE
            state.message = dup_msg or "Duplicate item detected"
            AuditService.save_workflow(state)
        return {
            "success": False,
            "status": "DUPLICATE",
            "message": dup_msg,
            "errors": [dup_msg]
        }

    # Step 19: Send POST request to SAP Business One Service Layer
    if state:
        state.status = WorkflowStatus.CREATING_IN_SAP
        AuditService.save_workflow(state)

    payload_hash = hash_payload(item_model.to_service_layer_payload())
    try:
        sap_response = await SAPItemsService.create_item(item_model)
        sap_obj_id = sap_response.get("ItemCode", item_model.ItemCode)
        
        # Audit record
        audit_record = AuditLogRecord(
            workflow_id=req.workflow_id or "direct_api",
            master_type="item",
            action="CREATE",
            payload_hash=payload_hash,
            sap_response_status=201,
            sap_object_id=sap_obj_id,
            success=True,
            details=f"Item {sap_obj_id} created successfully via Service Layer"
        )
        AuditService.record_audit(audit_record)

        if state:
            state.status = WorkflowStatus.CREATED
            state.sap_object_id = sap_obj_id
            state.sap_response_status = 201
            state.sap_response_body = sap_response
            state.message = f"Item {sap_obj_id} created successfully in SAP."
            AuditService.save_workflow(state)

        return {
            "success": True,
            "status": "CREATED",
            "message": f"Item {sap_obj_id} created successfully in SAP.",
            "data": {
                "sap_object_id": sap_obj_id,
                "master_type": "item",
                "sap_response": sap_response
            }
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Failed to create Item in SAP: {err_msg}")
        AuditService.record_audit(AuditLogRecord(
            workflow_id=req.workflow_id or "direct_api",
            master_type="item",
            action="CREATE",
            payload_hash=payload_hash,
            sap_response_status=500,
            success=False,
            details=err_msg
        ))
        if state:
            state.status = WorkflowStatus.SAP_ERROR
            state.error_details = err_msg
            state.message = f"Could not create the item in SAP. {err_msg}"
            AuditService.save_workflow(state)
            
        return {
            "success": False,
            "status": "SAP_ERROR",
            "message": f"Could not create the item in SAP. {err_msg}",
            "errors": [err_msg]
        }

@router.post("/master-data/business-partner/create")
async def create_bp_in_sap(req: MasterDataCreationRequest):
    """Create Business Partner in SAP Business One via Service Layer (/b1s/v2/BusinessPartners)."""
    state = None
    data = req.data

    if req.workflow_id:
        state = AuditService.get_workflow(req.workflow_id)
        if not state:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if not state.is_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Security Gate: Explicit user confirmation is required before posting to SAP."
            )
        data = state.final_payload or state.normalized_data

    if not data:
        raise HTTPException(status_code=400, detail="No Business Partner data provided.")

    val_res = validation_service.validate_business_partner(data)
    valid_data = val_res.validated_data or dict(data)
    bp_model = BusinessPartnerCreate(**valid_data)

    is_dup, dup_msg = await duplicate_service.check_duplicate(MasterDataType.BUSINESS_PARTNER, data)
    if is_dup:
        if state:
            state.status = WorkflowStatus.DUPLICATE
            state.message = dup_msg or "Duplicate business partner detected"
            AuditService.save_workflow(state)
        return {
            "success": False,
            "status": "DUPLICATE",
            "message": dup_msg,
            "errors": [dup_msg]
        }

    if state:
        state.status = WorkflowStatus.CREATING_IN_SAP
        AuditService.save_workflow(state)

    payload_hash = hash_payload(bp_model.to_service_layer_payload())
    try:
        sap_response = await SAPBusinessPartnersService.create_business_partner(bp_model)
        sap_obj_id = sap_response.get("CardCode", bp_model.CardCode)

        AuditService.record_audit(AuditLogRecord(
            workflow_id=req.workflow_id or "direct_api",
            master_type="business_partner",
            action="CREATE",
            payload_hash=payload_hash,
            sap_response_status=201,
            sap_object_id=sap_obj_id,
            success=True,
            details=f"Business Partner {sap_obj_id} created successfully via Service Layer"
        ))

        if state:
            state.status = WorkflowStatus.CREATED
            state.sap_object_id = sap_obj_id
            state.sap_response_status = 201
            state.sap_response_body = sap_response
            state.message = f"Business Partner {sap_obj_id} created successfully in SAP."
            AuditService.save_workflow(state)

        return {
            "success": True,
            "status": "CREATED",
            "message": f"Business Partner {sap_obj_id} created successfully in SAP.",
            "data": {
                "sap_object_id": sap_obj_id,
                "master_type": "business_partner",
                "sap_response": sap_response
            }
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Failed to create Business Partner in SAP: {err_msg}")
        AuditService.record_audit(AuditLogRecord(
            workflow_id=req.workflow_id or "direct_api",
            master_type="business_partner",
            action="CREATE",
            payload_hash=payload_hash,
            sap_response_status=500,
            success=False,
            details=err_msg
        ))
        if state:
            state.status = WorkflowStatus.SAP_ERROR
            state.error_details = err_msg
            state.message = f"Could not create Business Partner in SAP. {err_msg}"
            AuditService.save_workflow(state)

        return {
            "success": False,
            "status": "SAP_ERROR",
            "message": f"Could not create Business Partner in SAP. {err_msg}",
            "errors": [err_msg]
        }

@router.post("/master-data/warehouse/create")
async def create_warehouse_in_sap(req: MasterDataCreationRequest):
    """Create Warehouse in SAP Business One via Service Layer (/b1s/v2/Warehouses)."""
    state = None
    data = req.data

    if req.workflow_id:
        state = AuditService.get_workflow(req.workflow_id)
        if not state:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if not state.is_confirmed:
            raise HTTPException(
                status_code=400,
                detail="Security Gate: Explicit user confirmation is required before posting to SAP."
            )
        data = state.final_payload or state.normalized_data

    if not data:
        raise HTTPException(status_code=400, detail="No Warehouse data provided.")

    val_res = validation_service.validate_warehouse(data)
    valid_data = val_res.validated_data or dict(data)
    wh_model = WarehouseCreate(**valid_data)

    is_dup, dup_msg = await duplicate_service.check_duplicate(MasterDataType.WAREHOUSE, data)
    if is_dup:
        if state:
            state.status = WorkflowStatus.DUPLICATE
            state.message = dup_msg or "Duplicate warehouse detected"
            AuditService.save_workflow(state)
        return {
            "success": False,
            "status": "DUPLICATE",
            "message": dup_msg,
            "errors": [dup_msg]
        }

    if state:
        state.status = WorkflowStatus.CREATING_IN_SAP
        AuditService.save_workflow(state)

    payload_hash = hash_payload(wh_model.to_service_layer_payload())
    try:
        sap_response = await SAPWarehousesService.create_warehouse(wh_model)
        sap_obj_id = sap_response.get("WarehouseCode", wh_model.WarehouseCode)

        AuditService.record_audit(AuditLogRecord(
            workflow_id=req.workflow_id or "direct_api",
            master_type="warehouse",
            action="CREATE",
            payload_hash=payload_hash,
            sap_response_status=201,
            sap_object_id=sap_obj_id,
            success=True,
            details=f"Warehouse {sap_obj_id} created successfully via Service Layer"
        ))

        if state:
            state.status = WorkflowStatus.CREATED
            state.sap_object_id = sap_obj_id
            state.sap_response_status = 201
            state.sap_response_body = sap_response
            state.message = f"Warehouse {sap_obj_id} created successfully in SAP."
            AuditService.save_workflow(state)

        return {
            "success": True,
            "status": "CREATED",
            "message": f"Warehouse {sap_obj_id} created successfully in SAP.",
            "data": {
                "sap_object_id": sap_obj_id,
                "master_type": "warehouse",
                "sap_response": sap_response
            }
        }
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Failed to create Warehouse in SAP: {err_msg}")
        AuditService.record_audit(AuditLogRecord(
            workflow_id=req.workflow_id or "direct_api",
            master_type="warehouse",
            action="CREATE",
            payload_hash=payload_hash,
            sap_response_status=500,
            success=False,
            details=err_msg
        ))
        if state:
            state.status = WorkflowStatus.SAP_ERROR
            state.error_details = err_msg
            state.message = f"Could not create Warehouse in SAP. {err_msg}"
            AuditService.save_workflow(state)

        return {
            "success": False,
            "status": "SAP_ERROR",
            "message": f"Could not create Warehouse in SAP. {err_msg}",
            "errors": [err_msg]
        }

class LogActionRequest(BaseModel):
    workflow_id: Optional[str] = "manual"
    master_type: Optional[str] = "master_data"
    action: Optional[str] = "USER_ACTION"
    activity: str
    user_id: Optional[str] = None
    company_db: Optional[str] = None
    transaction_num: Optional[str] = None
    previous_value: Optional[Any] = None
    updated_value: Optional[Any] = None
    details: Optional[str] = None

@router.post("/audit/log-action")
async def log_user_action(req: LogActionRequest, x_user_id: Optional[str] = Header(None)):
    """
    Log client-side user activities (e.g. Copy Date & Item #, field corrections, UI transfers)
    with previous value and updated value.
    """
    u_id = x_user_id or req.user_id or "cinntra_user"
    c_db = req.company_db or settings.sap_company_db

    prev_val_str = json.dumps(req.previous_value) if isinstance(req.previous_value, (dict, list)) else (str(req.previous_value) if req.previous_value is not None else None)
    new_val_str = json.dumps(req.updated_value) if isinstance(req.updated_value, (dict, list)) else (str(req.updated_value) if req.updated_value is not None else None)

    audit_rec = AuditLogRecord(
        workflow_id=req.workflow_id or "manual",
        master_type=req.master_type or "master_data",
        action=req.action or "USER_ACTION",
        activity=req.activity,
        user_id=u_id,
        user_identifier=u_id,
        company_db=c_db,
        transaction_num=req.transaction_num,
        previous_value=prev_val_str,
        updated_value=new_val_str,
        success=True,
        details=req.details or f"Activity '{req.activity}' executed by user {u_id}"
    )
    AuditService.record_audit(audit_rec)
    return {"success": True, "status": "SUCCESS", "message": "Activity logged successfully."}

@router.get("/audit/logs")
async def list_audit_trail(
    limit: int = Query(default=100, ge=1, le=1000),
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Filter audit logs for the past N days"),
    user_id: Optional[str] = Query(default=None, description="Filter by User ID / Login ID"),
    company_db: Optional[str] = Query(default=None, description="Filter by SAP Company / Database"),
    activity: Optional[str] = Query(default=None, description="Filter by activity / action"),
    search: Optional[str] = Query(default=None, description="Search query across details and doc numbers")
):
    """Retrieve immutable audit records with comprehensive filtering options."""
    logs = AuditService.list_audit_logs(
        limit=limit,
        days=days,
        user_id=user_id,
        company_db=company_db,
        activity=activity,
        search=search
    )
    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Retrieved {len(logs)} audit records.",
        "company_db": settings.sap_company_db,
        "data": logs
    }

@router.get("/audit/download-log")
async def download_audit_log_file():
    """Download the raw persistent system audit log file (audit_trail.log)."""
    log_path = AuditService.get_audit_log_file_path()
    if not log_path.exists():
        # Create initial log entry if file doesn't exist
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] [SYSTEM] [DB:{settings.sap_company_db}] - Audit log initialized.\n")

    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    filename = f"SAP_Audit_Trail_{settings.sap_company_db}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/dashboard/stats")
async def get_dashboard_metrics(
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Retrieve dashboard stats for the past N days")
):
    """Retrieve platform dashboard metrics and statistics with live database records information and optional custom days filter."""
    stats = AuditService.get_dashboard_stats(days=days)
    
    # Query live SAP entity counts from connected SAP database
    try:
        sap_counts = await sap_client.get_entity_counts()
        stats["sap_counts"] = sap_counts
        stats["items_total"] = sap_counts.get("Items", stats.get("items_created", 0))
        stats["business_partners_total"] = sap_counts.get("BusinessPartners", stats.get("business_partners_created", 0))
        stats["warehouses_total"] = sap_counts.get("Warehouses", stats.get("warehouses_created", 0))
    except Exception as e:
        logger.warning(f"Could not fetch live SAP counts for dashboard: {e}")
        stats["sap_counts"] = {
            "Items": stats.get("items_created", 0),
            "BusinessPartners": stats.get("business_partners_created", 0),
            "Warehouses": stats.get("warehouses_created", 0)
        }
        stats["items_total"] = stats.get("items_created", 0)
        stats["business_partners_total"] = stats.get("business_partners_created", 0)
        stats["warehouses_total"] = stats.get("warehouses_created", 0)

    # Attach database environment context
    stats["database"] = {
        "company_db": settings.sap_company_db,
        "service_layer_url": settings.sap_service_layer_url,
        "is_configured": settings.is_sap_configured
    }

    # Query recent workflow documents
    try:
        stats["recent_workflows"] = AuditService.list_workflows(limit=10, days=days)
    except Exception as e:
        logger.warning(f"Could not fetch recent workflows for dashboard: {e}")
        stats["recent_workflows"] = []

    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Dashboard statistics retrieved successfully{' for past ' + str(days) + ' days' if days else ''}.",
        "data": stats
    }

ENTITY_ALIAS_MAP = {
    "items": "Items",
    "item": "Items",
    "oitm": "Items",
    "businesspartners": "BusinessPartners",
    "business_partners": "BusinessPartners",
    "businesspartner": "BusinessPartners",
    "business-partner": "BusinessPartners",
    "business_partner": "BusinessPartners",
    "bp": "BusinessPartners",
    "ocrd": "BusinessPartners",
    "warehouses": "Warehouses",
    "warehouse": "Warehouses",
    "wh": "Warehouses",
    "owhs": "Warehouses",
    "workflows": "Workflows",
    "workflow": "Workflows",
    "dashboard": "Dashboard",
    "all": "Dashboard",
}

def _style_excel_sheet(ws, header_row_idx: int = 1):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    regular_font = Font(name="Calibri", size=10.5, color="1E293B")
    thin_border_side = Side(style="thin", color="E2E8F0")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    ws.row_dimensions[header_row_idx].height = 24

    for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=ws.max_row), start=1):
        if row_idx == header_row_idx:
            for cell in row:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = cell_border
        elif row_idx > header_row_idx:
            ws.row_dimensions[row_idx].height = 19
            is_even = (row_idx - header_row_idx) % 2 == 0
            for cell in row:
                cell.font = regular_font
                cell.border = cell_border
                cell.alignment = Alignment(vertical="center")
                if is_even:
                    cell.fill = zebra_fill

    for col in ws.columns:
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 14), 45)


@router.get("/export/excel")
async def export_master_data_excel(
    entity: str = Query(default="Items", description="Entity: Items, BusinessPartners, Warehouses, Workflows, or Dashboard"),
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Filter by past N days"),
    search: Optional[str] = Query(default=None, description="Optional search term"),
    limit: int = Query(default=5000, ge=1, le=10000, description="Max records to export")
):
    """Generate and download a professional, styled Excel (.xlsx) file containing live SAP master data or workflows."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    raw_entity = entity.strip() if isinstance(entity, str) else "Items"
    entity_normalized = ENTITY_ALIAS_MAP.get(raw_entity.lower(), raw_entity)
    days_val = days if isinstance(days, int) and days > 0 else None
    search_val = search.strip() if isinstance(search, str) and search.strip() else None
    limit_val = limit if isinstance(limit, int) and limit > 0 else 5000
    
    wb = openpyxl.Workbook()
    total_record_count = 0

    if entity_normalized in ["Items", "BusinessPartners", "Warehouses"]:
        ws = wb.active
        res = await sap_client.get_live_records(entity=entity_normalized, top=limit_val, skip=0, search=search_val, days=days_val)
        records = res.get("records", [])
        total_record_count = len(records)

        if entity_normalized == "Items":
            ws.title = "Items Master (OITM)"
            headers = [
                "Item Code", "Item Description", "Item Group Code", "Inventory Item",
                "Sales Item", "Purchase Item", "Sales Unit (UoM)", "Purchase Unit",
                "Bar Code", "Tax Rate (%)", "Create Date", "Update Date", "Status"
            ]
            ws.append(headers)
            for r in records:
                ws.append([
                    str(r.get("ItemCode") or ""),
                    str(r.get("ItemName") or ""),
                    str(r.get("ItemsGroupCode") or ""),
                    "Yes" if r.get("InventoryItem") in ["tYES", True] else "No",
                    "Yes" if r.get("SalesItem") in ["tYES", True] else "No",
                    "Yes" if r.get("PurchaseItem") in ["tYES", True] else "No",
                    str(r.get("SalesUnit") or r.get("InventoryUOM") or ""),
                    str(r.get("PurchaseUnit") or ""),
                    str(r.get("BarCode") or ""),
                    str(r.get("TaxRate") or "0"),
                    str((r.get("CreateDate") or "")[:10]),
                    str((r.get("UpdateDate") or "")[:10]),
                    "Active"
                ])
            _style_excel_sheet(ws, header_row_idx=1)

        elif entity_normalized == "BusinessPartners":
            ws.title = "Business Partners (OCRD)"
            headers = [
                "Card Code", "Partner Name", "Card Type", "GSTIN / Federal Tax ID",
                "Phone Number", "Email Address", "Currency", "Street Address",
                "City", "Zip Code", "Create Date", "Update Date", "Status"
            ]
            ws.append(headers)
            for r in records:
                raw_type = r.get("CardType")
                card_type = "Customer" if raw_type == "cCustomer" else "Supplier" if raw_type == "cSupplier" else (raw_type or "Partner")
                ws.append([
                    str(r.get("CardCode") or ""),
                    str(r.get("CardName") or ""),
                    card_type,
                    str(r.get("FederalTaxID") or r.get("GSTNo") or ""),
                    str(r.get("Phone1") or ""),
                    str(r.get("EmailAddress") or ""),
                    str(r.get("Currency") or "INR"),
                    str(r.get("Address") or ""),
                    str(r.get("City") or ""),
                    str(r.get("ZipCode") or ""),
                    str((r.get("CreateDate") or "")[:10]),
                    str((r.get("UpdateDate") or "")[:10]),
                    "Active"
                ])
            _style_excel_sheet(ws, header_row_idx=1)

        elif entity_normalized == "Warehouses":
            ws.title = "Warehouses (OWHS)"
            headers = [
                "Warehouse Code", "Warehouse Name", "City", "State",
                "Street Address", "Zip Code", "Country", "Inactive", "Status"
            ]
            ws.append(headers)
            for r in records:
                inactive = r.get("Inactive", "tNO")
                is_inactive = inactive == "tYES" or inactive is True
                ws.append([
                    str(r.get("WarehouseCode") or ""),
                    str(r.get("WarehouseName") or ""),
                    str(r.get("City") or ""),
                    str(r.get("State") or ""),
                    str(r.get("Street") or ""),
                    str(r.get("ZipCode") or ""),
                    str(r.get("Country") or "IN"),
                    "Yes" if is_inactive else "No",
                    "Inactive" if is_inactive else "Active"
                ])
            _style_excel_sheet(ws, header_row_idx=1)

    elif entity_normalized == "Workflows":
        ws = wb.active
        ws.title = "Workflows Audit"
        raw_workflows = AuditService.list_workflows(limit=limit_val, offset=0, days=days_val)
        if search_val:
            s_lower = search_val.lower()
            records = [
                w for w in raw_workflows
                if s_lower in str(w.get("filename", "")).lower()
                or s_lower in str(w.get("workflow_id", "")).lower()
                or s_lower in str(w.get("sap_object_id", "")).lower()
            ]
        else:
            records = raw_workflows

        total_record_count = len(records)
        headers = [
            "Workflow ID", "Filename", "Master Type", "Processing Status",
            "SAP Object ID", "SAP Response Status", "User Confirmed", "Created At", "Updated At", "Execution Details"
        ]
        ws.append(headers)
        for r in records:
            ws.append([
                str(r.get("workflow_id") or ""),
                str(r.get("filename") or ""),
                str(r.get("master_type") or "").upper(),
                str(r.get("status") or ""),
                str(r.get("sap_object_id") or ""),
                str(r.get("sap_response_status") or ""),
                "Yes" if r.get("is_confirmed") else "No",
                str(r.get("created_at") or ""),
                str(r.get("updated_at") or ""),
                str(r.get("message") or "")
            ])
        _style_excel_sheet(ws, header_row_idx=1)

    elif entity_normalized == "Dashboard":
        counts = await sap_client.get_entity_counts()
        health = await sap_client.check_health()
        workflows = AuditService.list_workflows(limit=limit_val, offset=0, days=days_val)
        timeframe_label = f"Last {days_val} days" if days_val else "All time"

        # Sheet 1: Executive Overview
        ws_overview = wb.active
        ws_overview.title = "Executive Overview"
        ws_overview.append(["SAP AI MASTER DATA PLATFORM - EXECUTIVE DASHBOARD REPORT"])
        ws_overview.append(["Export Timestamp", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")])
        ws_overview.append(["Target Company Database", str(health.get("company_db") or settings.sap_company_db)])
        ws_overview.append(["SAP Service Layer URL", str(health.get("service_layer_url") or settings.sap_service_layer_url)])
        ws_overview.append(["Live Connection Status", "Connected (Live SAP)" if health.get("connected") else "Simulated Sandbox / Disconnected"])
        ws_overview.append(["Active Timeframe Scope", timeframe_label])
        ws_overview.append([])

        ws_overview.append(["MASTER DATA KPI METRICS", "TOTAL COUNT", "DATA SOURCE / CATEGORY"])
        ws_overview.append(["Items Master Catalog (OITM)", counts.get("Items", 0), "SAP Service Layer"])
        ws_overview.append(["Business Partners (OCRD)", counts.get("BusinessPartners", 0), "SAP Service Layer"])
        ws_overview.append(["Warehouse Facilities (OWHS)", counts.get("Warehouses", 0), "SAP Service Layer"])
        ws_overview.append(["Workflow Documents Processed", len(workflows), "AI Master Ingestion Engine"])
        ws_overview.append([])
        _style_excel_sheet(ws_overview, header_row_idx=8)

        # Sheet 2: Items Master (OITM)
        try:
            items_res = await sap_client.get_live_records(entity="Items", top=limit_val, skip=0, search=search_val, days=days_val)
            item_records = items_res.get("records", [])
            ws_items = wb.create_sheet(title="Items Master (OITM)")
            ws_items.append([
                "Item Code", "Item Description", "Item Group Code", "Inventory Item",
                "Sales Item", "Purchase Item", "Sales Unit (UoM)", "Purchase Unit",
                "Bar Code", "Tax Rate (%)", "Create Date", "Update Date", "Status"
            ])
            for r in item_records:
                ws_items.append([
                    str(r.get("ItemCode") or ""),
                    str(r.get("ItemName") or ""),
                    str(r.get("ItemsGroupCode") or ""),
                    "Yes" if r.get("InventoryItem") in ["tYES", True] else "No",
                    "Yes" if r.get("SalesItem") in ["tYES", True] else "No",
                    "Yes" if r.get("PurchaseItem") in ["tYES", True] else "No",
                    str(r.get("SalesUnit") or r.get("InventoryUOM") or ""),
                    str(r.get("PurchaseUnit") or ""),
                    str(r.get("BarCode") or ""),
                    str(r.get("TaxRate") or "0"),
                    str((r.get("CreateDate") or "")[:10]),
                    str((r.get("UpdateDate") or "")[:10]),
                    "Active"
                ])
            _style_excel_sheet(ws_items, header_row_idx=1)
        except Exception as e:
            logger.warning(f"Failed to populate items sheet: {e}")

        # Sheet 3: Business Partners (OCRD)
        try:
            bp_res = await sap_client.get_live_records(entity="BusinessPartners", top=limit_val, skip=0, search=search_val, days=days_val)
            bp_records = bp_res.get("records", [])
            ws_bp = wb.create_sheet(title="Business Partners (OCRD)")
            ws_bp.append([
                "Card Code", "Partner Name", "Card Type", "GSTIN / Federal Tax ID",
                "Phone Number", "Email Address", "Currency", "Street Address",
                "City", "Zip Code", "Create Date", "Update Date", "Status"
            ])
            for r in bp_records:
                raw_type = r.get("CardType")
                card_type = "Customer" if raw_type == "cCustomer" else "Supplier" if raw_type == "cSupplier" else (raw_type or "Partner")
                ws_bp.append([
                    str(r.get("CardCode") or ""),
                    str(r.get("CardName") or ""),
                    card_type,
                    str(r.get("FederalTaxID") or r.get("GSTNo") or ""),
                    str(r.get("Phone1") or ""),
                    str(r.get("EmailAddress") or ""),
                    str(r.get("Currency") or "INR"),
                    str(r.get("Address") or ""),
                    str(r.get("City") or ""),
                    str(r.get("ZipCode") or ""),
                    str((r.get("CreateDate") or "")[:10]),
                    str((r.get("UpdateDate") or "")[:10]),
                    "Active"
                ])
            _style_excel_sheet(ws_bp, header_row_idx=1)
        except Exception as e:
            logger.warning(f"Failed to populate BP sheet: {e}")

        # Sheet 4: Warehouses (OWHS)
        try:
            wh_res = await sap_client.get_live_records(entity="Warehouses", top=limit_val, skip=0, search=search_val, days=days_val)
            wh_records = wh_res.get("records", [])
            ws_wh = wb.create_sheet(title="Warehouses (OWHS)")
            ws_wh.append([
                "Warehouse Code", "Warehouse Name", "City", "State",
                "Street Address", "Zip Code", "Country", "Inactive", "Status"
            ])
            for r in wh_records:
                inactive = r.get("Inactive", "tNO")
                is_inactive = inactive == "tYES" or inactive is True
                ws_wh.append([
                    str(r.get("WarehouseCode") or ""),
                    str(r.get("WarehouseName") or ""),
                    str(r.get("City") or ""),
                    str(r.get("State") or ""),
                    str(r.get("Street") or ""),
                    str(r.get("ZipCode") or ""),
                    str(r.get("Country") or "IN"),
                    "Yes" if is_inactive else "No",
                    "Inactive" if is_inactive else "Active"
                ])
            _style_excel_sheet(ws_wh, header_row_idx=1)
        except Exception as e:
            logger.warning(f"Failed to populate warehouses sheet: {e}")

        # Sheet 5: Workflows Audit
        ws_wf = wb.create_sheet(title="Workflows & Ingestion")
        ws_wf.append([
            "Workflow ID", "Filename", "Master Type", "Status", "SAP Object ID", "SAP Response", "Confirmed", "Created At"
        ])
        for r in workflows:
            ws_wf.append([
                str(r.get("workflow_id") or ""),
                str(r.get("filename") or ""),
                str(r.get("master_type") or "").upper(),
                str(r.get("status") or ""),
                str(r.get("sap_object_id") or ""),
                str(r.get("sap_response_status") or ""),
                "Yes" if r.get("is_confirmed") else "No",
                str(r.get("created_at") or "")
            ])
        _style_excel_sheet(ws_wf, header_row_idx=1)
        total_record_count = counts.get("Items", 0) + counts.get("BusinessPartners", 0) + counts.get("Warehouses", 0) + len(workflows)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported entity '{entity}'. Choose Items, BusinessPartners, Warehouses, Workflows, or Dashboard.")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    timeframe_slug = f"last_{days}_days" if days else "all_time"
    filename = f"SAP_{entity_normalized}_{timeframe_slug}_{datetime.utcnow().strftime('%Y%m%d')}.xlsx"

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition, X-Total-Count",
            "X-Total-Count": str(total_record_count)
        }
    )

@router.get("/export/csv")
async def export_master_data_csv(
    entity: str = Query(default="Dashboard", description="Entity: Dashboard, Items, BusinessPartners, Warehouses, or Workflows"),
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Filter by past N days"),
    search: Optional[str] = Query(default=None, description="Optional search term"),
    limit: int = Query(default=1000, ge=1, le=5000, description="Max records to export")
):
    """Generate and download a real CSV file containing live SAP master data or workflows filtered by custom days."""
    raw_entity = entity.strip()
    entity_normalized = ENTITY_ALIAS_MAP.get(raw_entity.lower(), raw_entity)
    
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    records = []
    
    if entity_normalized in ["Items", "BusinessPartners", "Warehouses"]:
        res = await sap_client.get_live_records(entity=entity_normalized, top=limit, skip=0, search=search, days=days)
        records = res.get("records", [])
        
        if entity_normalized == "Items":
            headers = ["ItemCode", "ItemName", "ItemsGroupCode", "InventoryItem", "SalesItem", "PurchaseItem", "SalesUnit", "PurchaseUnit", "BarCode", "TaxRate", "CreateDate", "UpdateDate", "Status"]
            writer.writerow(headers)
            for r in records:
                writer.writerow([
                    r.get("ItemCode", ""),
                    r.get("ItemName", ""),
                    r.get("ItemsGroupCode", ""),
                    "Yes" if r.get("InventoryItem") in ["tYES", True] else "No",
                    "Yes" if r.get("SalesItem") in ["tYES", True] else "No",
                    "Yes" if r.get("PurchaseItem") in ["tYES", True] else "No",
                    r.get("SalesUnit", "") or r.get("InventoryUOM", ""),
                    r.get("PurchaseUnit", ""),
                    r.get("BarCode", "") or "",
                    r.get("TaxRate", "0"),
                    (r.get("CreateDate") or "")[:10],
                    (r.get("UpdateDate") or "")[:10],
                    "Active"
                ])
        elif entity_normalized == "BusinessPartners":
            headers = ["CardCode", "CardName", "CardType", "FederalTaxID", "Phone1", "EmailAddress", "Currency", "Address", "City", "ZipCode", "CreateDate", "UpdateDate", "Status"]
            writer.writerow(headers)
            for r in records:
                raw_type = r.get("CardType")
                card_type = "Customer" if raw_type == "cCustomer" else "Supplier" if raw_type == "cSupplier" else (raw_type or "Partner")
                writer.writerow([
                    r.get("CardCode", ""),
                    r.get("CardName", ""),
                    card_type,
                    r.get("FederalTaxID", "") or r.get("GSTNo", ""),
                    r.get("Phone1", "") or "",
                    r.get("EmailAddress", "") or "",
                    r.get("Currency", "") or "INR",
                    r.get("Address", "") or "",
                    r.get("City", "") or "",
                    r.get("ZipCode", "") or "",
                    (r.get("CreateDate") or "")[:10],
                    (r.get("UpdateDate") or "")[:10],
                    "Active"
                ])
        elif entity_normalized == "Warehouses":
            headers = ["WarehouseCode", "WarehouseName", "City", "State", "Street", "ZipCode", "Country", "Inactive", "Status"]
            writer.writerow(headers)
            for r in records:
                inactive = r.get("Inactive", "tNO")
                is_inactive = inactive == "tYES" or inactive is True
                writer.writerow([
                    r.get("WarehouseCode", ""),
                    r.get("WarehouseName", ""),
                    r.get("City", "") or "",
                    r.get("State", "") or "",
                    r.get("Street", "") or "",
                    r.get("ZipCode", "") or "",
                    r.get("Country", "IN"),
                    "Yes" if is_inactive else "No",
                    "Inactive" if is_inactive else "Active"
                ])
    elif entity_normalized == "Workflows":
        raw_workflows = AuditService.list_workflows(limit=limit, offset=0, days=days)
        if search:
            s_lower = search.lower()
            records = [
                w for w in raw_workflows
                if s_lower in str(w.get("filename", "")).lower()
                or s_lower in str(w.get("workflow_id", "")).lower()
                or s_lower in str(w.get("sap_object_id", "")).lower()
            ]
        else:
            records = raw_workflows

        headers = ["WorkflowID", "Filename", "MasterType", "Status", "SAPObjectID", "SAPResponseStatus", "IsConfirmed", "CreatedAt", "UpdatedAt", "Message"]
        writer.writerow(headers)
        for r in records:
            writer.writerow([
                r.get("workflow_id", ""),
                r.get("filename", ""),
                r.get("master_type", ""),
                r.get("status", ""),
                r.get("sap_object_id", "") or "",
                r.get("sap_response_status", "") or "",
                "Yes" if r.get("is_confirmed") else "No",
                r.get("created_at", "") or "",
                r.get("updated_at", "") or "",
                r.get("message", "") or ""
            ])
    elif entity_normalized == "Dashboard":
        counts = await sap_client.get_entity_counts()
        health = await sap_client.check_health()
        workflows = AuditService.list_workflows(limit=limit, offset=0, days=days)
        timeframe_label = f"Last {days} days" if days else "All time"
        
        writer.writerow(["=== SAP AI MASTER DATA PLATFORM - EXECUTIVE DASHBOARD REPORT ==="])
        writer.writerow(["Export Generated At", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')])
        writer.writerow(["Company Database", health.get("company_db") or settings.sap_company_db])
        writer.writerow(["Service Layer Endpoint", health.get("service_layer_url") or settings.sap_service_layer_url])
        writer.writerow(["Connection Status", "Live Connected" if health.get("connected") else "Not Connected"])
        writer.writerow(["Timeframe Filter", timeframe_label])
        writer.writerow([])
        writer.writerow(["=== EXECUTIVE KPI METRICS ==="])
        writer.writerow(["Metric", "Count / Value", "Category"])
        writer.writerow(["Item Master Catalog (OITM)", counts.get("Items", 0), "Master Data"])
        writer.writerow(["Business Partners (OCRD)", counts.get("BusinessPartners", 0), "Master Data"])
        writer.writerow(["Warehouse Facilities (OWHS)", counts.get("Warehouses", 0), "Master Data"])
        writer.writerow(["Workflow Documents Processed", len(workflows), "Automation Pipeline"])
        writer.writerow([])
        writer.writerow(["=== RECENT WORKFLOWS & MASTER DATA INGESTION ACTIVITY ==="])
        headers = ["WorkflowID", "Filename", "MasterType", "Status", "SAPObjectID", "SAPResponseStatus", "IsConfirmed", "CreatedAt"]
        writer.writerow(headers)
        for r in workflows:
            writer.writerow([
                r.get("workflow_id", ""),
                r.get("filename", ""),
                r.get("master_type", ""),
                r.get("status", ""),
                r.get("sap_object_id", "") or "",
                r.get("sap_response_status", "") or "",
                "Yes" if r.get("is_confirmed") else "No",
                r.get("created_at", "") or ""
            ])
        records = workflows
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported entity '{entity}'. Choose Dashboard, Items, BusinessPartners, Warehouses, or Workflows.")
    
    timeframe_slug = f"last_{days}_days" if days else "all_time"
    filename = f"SAP_{entity_normalized}_{timeframe_slug}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition, X-Total-Count",
            "X-Total-Count": str(len(records))
        }
    )

@router.get("/export/json")
async def export_master_data_json(
    entity: str = Query(default="Dashboard", description="Entity: Dashboard, Items, BusinessPartners, Warehouses, or Workflows"),
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Filter by past N days"),
    limit: int = Query(default=1000, ge=1, le=5000, description="Max records to export")
):
    """Retrieve structured real SAP master data or workflows for JSON export."""
    raw_entity = entity.strip()
    entity_normalized = ENTITY_ALIAS_MAP.get(raw_entity.lower(), raw_entity)
    
    if entity_normalized in ["Items", "BusinessPartners", "Warehouses"]:
        res = await sap_client.get_live_records(entity=entity_normalized, top=limit, skip=0, days=days)
        records = res.get("records", [])
        total = res.get("total", len(records))
    elif entity_normalized == "Workflows":
        records = AuditService.list_workflows(limit=limit, offset=0, days=days)
        total = len(records)
    elif entity_normalized == "Dashboard":
        counts = await sap_client.get_entity_counts()
        health = await sap_client.check_health()
        stats = AuditService.get_dashboard_stats(days=days)
        workflows = AuditService.list_workflows(limit=limit, offset=0, days=days)
        return {
            "success": True,
            "entity": "Dashboard",
            "timeframe": {
                "days": days,
                "label": f"Last {days} days" if days else "All time"
            },
            "exported_at": datetime.utcnow().isoformat(),
            "database": {
                "company_db": health.get("company_db") or settings.sap_company_db,
                "service_layer_url": health.get("service_layer_url") or settings.sap_service_layer_url,
                "connected": health.get("connected", False),
                "status": health.get("status")
            },
            "kpi_summary": {
                "items_total": counts.get("Items", 0),
                "business_partners_total": counts.get("BusinessPartners", 0),
                "warehouses_total": counts.get("Warehouses", 0),
                "documents_processed": stats.get("documents_processed", len(workflows))
            },
            "recent_workflows": workflows,
            "stats": stats
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported entity '{entity}'. Choose Dashboard, Items, BusinessPartners, Warehouses, or Workflows.")
    
    return {
        "success": True,
        "entity": entity_normalized,
        "timeframe": {
            "days": days,
            "label": f"Last {days} days" if days else "All time"
        },
        "exported_at": datetime.utcnow().isoformat(),
        "total_records": total,
        "records": records
    }
