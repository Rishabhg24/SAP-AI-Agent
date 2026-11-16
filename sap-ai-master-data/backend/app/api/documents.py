"""
Document and workflow upload endpoints.
Handles PDF uploading, 3-way extraction, consensus comparison, and conflict resolution.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from app.config import settings
from app.models.extraction import ConflictStatus, MasterDataType
from app.models.workflow import WorkflowState, WorkflowStatus
from app.services.audit_service import AuditService
from app.services.chat_service import nvidia_chat_service
from app.services.extraction_compare import extraction_comparator
from app.services.extraction_service import extraction_service
from app.services.normalization_service import normalization_service
from app.services.pdf_service import pdf_service
from app.services.validation_service import validation_service
from app.utils.logging import logger
from app.utils.security import generate_uuid

router = APIRouter(prefix="/api", tags=["Documents & Workflows"])

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    master_type: Optional[str] = Form(None),
    use_ai: Optional[bool] = Form(False),
    prompt_instructions: Optional[str] = Form(None)
):
    """
    Upload a PDF or Excel (.xlsx, .csv) document containing SAP master data.
    Executes:
    1. Security & format validation (PDF / Excel magic bytes and integrity)
    2. Dynamic AI extraction via Nemotron (if enabled or needed) + 3-Way independent extraction
    3. Normalization layer & consensus comparison
    4. Deterministic Pydantic validation
    5. Workflow state machine progression
    """
    # Validate and save document (PDF or Excel)
    is_valid, msg, file_info = await pdf_service.save_and_validate_document(file)
    if not is_valid:
        return {
            "success": False,
            "status": "VALIDATION_ERROR",
            "message": msg,
            "errors": [msg]
        }

    workflow_id = file_info["uuid"]
    file_path = file_info["saved_path"]

    # Parse preferred master_type if user supplied one
    selected_type: Optional[MasterDataType] = None
    if master_type and master_type != "auto":
        try:
            selected_type = MasterDataType(master_type.lower())
        except ValueError:
            selected_type = None

    # Step 1: Run 3 independent extractors (AI-driven header mapping + regex fallback)
    extractions = await extraction_service.extract_all(file_path, master_type=selected_type)
    raw_extractions = {ext.method: ext.model_dump() for ext in extractions}

    # Step 2: Normalize and compare extraction outputs
    comparison = extraction_comparator.compare_extractions(extractions)
    detected_type = comparison.master_type or selected_type or MasterDataType.BUSINESS_PARTNER
    ai_enhanced = False

    # Step 3: Dynamic Nemotron LLM Ingestion (if use_ai is requested, or if 0 records extracted by rules)
    raw_text = pdf_service.extract_raw_text(file_path)
    if (use_ai or (not comparison.all_records and not comparison.agreed_data)) and raw_text.strip():
        try:
            pref_entity_str = detected_type.value if detected_type else (master_type or None)
            ai_data = await nvidia_chat_service.transform_document_to_sap_records(
                raw_document_text=raw_text,
                preferred_entity=pref_entity_str,
                custom_instructions=prompt_instructions
            )
            ai_records = ai_data.get("records", [])
            if ai_records and len(ai_records) > 0:
                ai_enhanced = True
                comparison.all_records = ai_records
                comparison.total_records = len(ai_records)
                comparison.agreed_data = ai_records[0]
                if "master_type" in ai_data:
                    try:
                        detected_type = MasterDataType(ai_data["master_type"].lower())
                        comparison.master_type = detected_type
                    except Exception:
                        pass
                logger.info(f"Nemotron dynamic ingestion successfully extracted {len(ai_records)} SAP records.")
        except Exception as ai_err:
            logger.warning(f"Nemotron dynamic ingestion encountered error, falling back to rule extraction: {ai_err}")

    # Initialize workflow state
    state = WorkflowState(
        workflow_id=workflow_id,
        filename=file_info["original_filename"],
        file_path=file_path,
        file_hash=file_info["file_hash"],
        master_type=detected_type,
        raw_extractions=raw_extractions,
        extraction_comparison=comparison,
        normalized_data=comparison.agreed_data,
        extracted_records=comparison.all_records,
        total_records=comparison.total_records
    )

    # Step 4: Check for extraction conflicts (if purely rule-based)
    if not ai_enhanced and comparison.status == ConflictStatus.CONFLICT:
        state.status = WorkflowStatus.EXTRACTION_CONFLICT
        state.message = f"Found conflicting values across extraction methods in {len(comparison.conflicts)} fields."
        AuditService.save_workflow(state)
        return {
            "success": True,
            "status": state.status.value,
            "message": state.message,
            "data": {
                "workflow_id": workflow_id,
                "master_type": detected_type.value,
                "status": state.status.value,
                "conflicts": [c.model_dump() for c in comparison.conflicts],
                "confidence": comparison.overall_confidence,
                "agreed_data": comparison.agreed_data,
                "extracted_records": comparison.all_records,
                "total_records": comparison.total_records,
                "ai_enhanced": ai_enhanced
            }
        }

    # Step 5: Proceed to deterministic enrichment and direct SAP readiness
    val_result = validation_service.validate(detected_type, comparison.agreed_data)
    state.validation_result = val_result
    state.missing_fields = []

    # Compute bulk validation if multiple records detected
    bulk_val = None
    if comparison.all_records and len(comparison.all_records) > 0:
        bulk_val = validation_service.validate_bulk(detected_type, comparison.all_records)
        state.bulk_validation = bulk_val

    state.status = WorkflowStatus.READY_FOR_CONFIRMATION
    state.final_payload = val_result.validated_data
    rec_count = len(comparison.all_records) if comparison.all_records else 1
    state.message = f"{rec_count} record(s) parsed and ready to post directly to SAP."

    AuditService.save_workflow(state)

    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": {
            "workflow_id": workflow_id,
            "master_type": detected_type.value,
            "status": state.status.value,
            "data": comparison.agreed_data,
            "validation": val_result.model_dump(),
            "missing_fields": [m.model_dump() for m in val_result.missing_fields],
            "bulk_validation": bulk_val.model_dump() if bulk_val else None,
            "confidence": comparison.overall_confidence,
            "extracted_records": comparison.all_records,
            "total_records": comparison.total_records,
            "ai_enhanced": ai_enhanced
        }
    }

@router.get("/workflows/{workflow_id}")
async def get_workflow_details(workflow_id: str):
    """Retrieve the complete workflow state by ID."""
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": state.model_dump()
    }

@router.post("/workflows/{workflow_id}/resolve-conflict")
async def resolve_extraction_conflict(workflow_id: str, payload: Dict[str, Any]):
    """
    User submits corrections for fields that had extraction disagreements.
    Re-runs comparison, normalization, and validation.
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    corrections = payload.get("corrections", {})
    state.user_corrections.update(corrections)

    # Reconstruct extraction outputs from stored dictionary
    from app.models.extraction import SingleExtractorOutput
    outputs = [SingleExtractorOutput(**ext) for ext in state.raw_extractions.values()]

    # Re-run comparison incorporating user corrections
    comparison = extraction_comparator.compare_extractions(outputs, user_corrections=state.user_corrections)
    state.extraction_comparison = comparison
    state.normalized_data = comparison.agreed_data

    # Check if any conflicts remain
    if comparison.status == ConflictStatus.CONFLICT:
        state.status = WorkflowStatus.EXTRACTION_CONFLICT
        state.message = f"{len(comparison.conflicts)} conflicting fields remain to be resolved."
        AuditService.save_workflow(state)
        return {
            "success": True,
            "status": state.status.value,
            "message": state.message,
            "data": {
                "workflow_id": workflow_id,
                "conflicts": [c.model_dump() for c in comparison.conflicts]
            }
        }

    # All conflicts resolved, proceed to validation
    val_result = validation_service.validate(state.master_type, comparison.agreed_data)
    state.validation_result = val_result
    state.status = WorkflowStatus.READY_FOR_CONFIRMATION
    state.final_payload = val_result.validated_data
    state.missing_fields = []
    state.message = "All conflicts resolved and data ready. Ready for confirmation."

    AuditService.save_workflow(state)

    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": {
            "workflow_id": workflow_id,
            "status": state.status.value,
            "data": state.normalized_data,
            "validation": val_result.model_dump(),
            "missing_fields": [m.model_dump() for m in val_result.missing_fields]
        }
    }

@router.get("/workflows")
async def list_workflows(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    days: Optional[int] = Query(default=None, ge=1, le=730, description="Filter workflows by last N days")
):
    """List recent document extraction workflows from local database with optional custom days filtering."""
    workflows = AuditService.list_workflows(limit=limit, offset=offset, days=days)
    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Retrieved {len(workflows)} workflow records.",
        "data": workflows
    }

@router.get("/documents/sample/{master_type}")
async def get_sample_document(
    master_type: str,
    format: str = Query(default="excel", description="Format: 'pdf', 'excel', or 'csv'"),
    mode: str = Query(default="bulk", description="Mode: 'bulk' or 'single'")
):
    """Retrieve sample PDF, Excel, or CSV document for a specific master data type for testing."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    from app.config import settings

    fmt_lower = format.lower()
    is_csv = fmt_lower == "csv"
    is_excel = fmt_lower in ["excel", "xlsx"]
    is_bulk = mode.lower() == "bulk"

    if is_csv:
        mapping = {
            "item": "sample_items_bulk.csv" if is_bulk else "sample_items_bulk.csv",
            "business_partner": "sample_suppliers_bulk.csv" if is_bulk else "sample_suppliers_bulk.csv",
            "warehouse": "sample_warehouses_bulk.csv" if is_bulk else "sample_warehouses_bulk.csv"
        }
        media_type = "text/csv"
    elif is_excel:
        mapping = {
            "item": "sample_items_bulk.xlsx" if is_bulk else "sample_item.xlsx",
            "business_partner": "sample_suppliers_bulk.xlsx" if is_bulk else "sample_supplier.xlsx",
            "warehouse": "sample_warehouses_bulk.xlsx" if is_bulk else "sample_warehouse.xlsx"
        }
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        mapping = {
            "item": "sample_item.pdf",
            "business_partner": "sample_supplier.pdf",
            "warehouse": "sample_warehouse.pdf"
        }
        media_type = "application/pdf"

    filename = mapping.get(master_type.lower())
    if not filename:
        raise HTTPException(status_code=404, detail=f"No sample document for master type '{master_type}'")

    file_path = pdf_service.upload_dir / filename
    if not file_path.exists():
        file_path = Path(settings.upload_dir) / filename
    if not file_path.exists():
        # Also check relative to backend directory
        backend_dir = Path(__file__).resolve().parent.parent.parent
        file_path = backend_dir / "uploads" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample {format.upper()} document '{filename}' not found on server.")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )

@router.post("/workflows/{workflow_id}/select-record")
async def select_workflow_record(workflow_id: str, payload: Dict[str, Any]):
    """
    Select an active record from extracted_records by index or record payload,
    re-running deterministic validation.
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    index = payload.get("index", 0)
    if state.extracted_records and 0 <= index < len(state.extracted_records):
        selected_record = state.extracted_records[index]
    else:
        selected_record = payload.get("record", state.normalized_data)

    state.normalized_data = selected_record
    val_result = validation_service.validate(state.master_type, selected_record)
    state.validation_result = val_result
    state.missing_fields = []
    state.status = WorkflowStatus.READY_FOR_CONFIRMATION
    state.final_payload = val_result.validated_data
    state.message = f"Record #{index + 1} ready for confirmation."

    AuditService.save_workflow(state)
    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": state.model_dump()
    }

@router.post("/workflows/{workflow_id}/bulk-apply-defaults")
@router.post("/workflows/{workflow_id}/apply-defaults")
async def bulk_apply_defaults(workflow_id: str, payload: Dict[str, Any]):
    """
    Apply common default values across all extracted records in a workflow.
    Useful for batch-enriching datasets missing non-primary attributes
    (e.g., CardType, default EmailAddress, or generating CardNames).
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    defaults = payload.get("defaults") if isinstance(payload.get("defaults"), dict) else payload
    if not defaults:
        raise HTTPException(status_code=400, detail="No defaults provided")

    card_name_prefix = defaults.get("CardNamePrefix", "")
    email_address = defaults.get("EmailAddress")
    card_type = defaults.get("CardType")
    items_group_code = defaults.get("ItemsGroupCode")
    currency = defaults.get("Currency")

    records = list(state.extracted_records or [state.normalized_data])
    updated_records = []

    for idx, rec in enumerate(records):
        new_rec = dict(rec)
        
        # Apply CardType if relevant
        if card_type and not new_rec.get("CardType"):
            new_rec["CardType"] = card_type

        # Apply or generate CardName if missing
        if not new_rec.get("CardName"):
            if card_name_prefix:
                code = str(new_rec.get("CardCode") or f"{idx + 1}")
                new_rec["CardName"] = f"{card_name_prefix}{code}".strip()
            elif defaults.get("CardName"):
                new_rec["CardName"] = defaults.get("CardName")

        # Apply default email if missing
        if email_address and not new_rec.get("EmailAddress"):
            new_rec["EmailAddress"] = email_address

        # Apply ItemsGroupCode if missing
        if items_group_code and not new_rec.get("ItemsGroupCode"):
            new_rec["ItemsGroupCode"] = items_group_code

        # Apply Currency if missing
        if currency and not new_rec.get("Currency"):
            new_rec["Currency"] = currency

        # Apply any arbitrary extra field
        for k, v in defaults.items():
            if k not in ["CardNamePrefix"] and (new_rec.get(k) is None or new_rec.get(k) == ""):
                new_rec[k] = v

        # Auto-extract PAN from 15-char GSTIN if PAN is missing
        fed_id = new_rec.get("FederalTaxID") or new_rec.get("GSTNo")
        if fed_id and len(str(fed_id).strip()) == 15 and not new_rec.get("PANNo"):
            new_rec["PANNo"] = str(fed_id).strip()[2:12].upper()
        if fed_id and len(str(fed_id).strip()) == 15 and not new_rec.get("GSTNo"):
            new_rec["GSTNo"] = str(fed_id).strip().upper()

        norm_rec = normalization_service.normalize_dict(new_rec)
        updated_records.append(norm_rec)

    state.extracted_records = updated_records
    if updated_records:
        state.normalized_data = updated_records[0]

    # Re-run bulk validation
    bulk_val = validation_service.validate_bulk(state.master_type, updated_records)
    state.bulk_validation = bulk_val

    # Re-validate active record
    val_res = validation_service.validate(state.master_type, state.normalized_data)
    state.validation_result = val_res
    state.missing_fields = val_res.missing_fields

    if bulk_val.valid_count == bulk_val.total:
        state.status = WorkflowStatus.READY_FOR_CONFIRMATION
        state.message = f"All {bulk_val.total} records validated successfully with batch defaults. Ready for confirmation."
        if val_res.valid:
            state.final_payload = val_res.validated_data
    elif val_res.valid:
        state.status = WorkflowStatus.READY_FOR_CONFIRMATION
        state.message = f"{bulk_val.valid_count} of {bulk_val.total} records valid. Ready for confirmation."
        state.final_payload = val_res.validated_data
    else:
        state.status = WorkflowStatus.MISSING_FIELDS
        state.message = f"Defaults applied. {bulk_val.valid_count}/{bulk_val.total} records valid, but {len(val_res.missing_fields)} fields still missing in active record."

    AuditService.save_workflow(state)
    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": state.model_dump()
    }

@router.post("/workflows/{workflow_id}/update-record")
async def update_workflow_record(workflow_id: str, payload: Dict[str, Any]):
    """
    Directly update one or more fields in a workflow record (or all records),
    running normalization and re-validating deterministic rules.
    Used for inline table editing and direct missing-fields table submission.
    """
    state = AuditService.get_workflow(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")

    records_list = payload.get("records")
    updates = payload.get("updates", {})
    record_index = payload.get("index")
    apply_to_all = payload.get("apply_to_all", False)

    existing_records = list(state.extracted_records or [state.normalized_data])

    if records_list and isinstance(records_list, list):
        # Full table replacement from spreadsheet table editor
        updated_records = []
        for r in records_list:
            norm_r = normalization_service.normalize_dict(r)
            fed_id = norm_r.get("FederalTaxID") or norm_r.get("GSTNo")
            if fed_id and len(str(fed_id).strip()) == 15 and not norm_r.get("PANNo"):
                norm_r["PANNo"] = str(fed_id).strip()[2:12].upper()
            if fed_id and len(str(fed_id).strip()) == 15 and not norm_r.get("GSTNo"):
                norm_r["GSTNo"] = str(fed_id).strip().upper()
            updated_records.append(norm_r)
        state.extracted_records = updated_records
        active_idx = record_index if (record_index is not None and 0 <= record_index < len(updated_records)) else 0
        state.normalized_data = updated_records[active_idx]
    elif apply_to_all:
        updated_records = []
        card_name_prefix = updates.get("CardNamePrefix", "")
        for idx, rec in enumerate(existing_records):
            new_rec = dict(rec)
            for k, v in updates.items():
                if k != "CardNamePrefix" and v is not None and v != "":
                    new_rec[k] = v
            # Generate CardName if missing
            if not new_rec.get("CardName"):
                if card_name_prefix:
                    code = str(new_rec.get("CardCode") or f"{idx + 1}")
                    new_rec["CardName"] = f"{card_name_prefix}{code}".strip()
                elif updates.get("CardName"):
                    new_rec["CardName"] = updates.get("CardName")
            # Auto-extract PAN from 15-char GSTIN
            fed_id = new_rec.get("FederalTaxID") or new_rec.get("GSTNo")
            if fed_id and len(str(fed_id).strip()) == 15 and not new_rec.get("PANNo"):
                new_rec["PANNo"] = str(fed_id).strip()[2:12].upper()
            if fed_id and len(str(fed_id).strip()) == 15 and not new_rec.get("GSTNo"):
                new_rec["GSTNo"] = str(fed_id).strip().upper()
            norm_rec = normalization_service.normalize_dict(new_rec)
            updated_records.append(norm_rec)
        state.extracted_records = updated_records
        active_idx = record_index if (record_index is not None and 0 <= record_index < len(updated_records)) else 0
        state.normalized_data = updated_records[active_idx]
    else:
        # Single record update
        idx = record_index if (record_index is not None and 0 <= record_index < len(existing_records)) else 0
        rec_to_update = dict(existing_records[idx] if existing_records else state.normalized_data)
        for k, v in updates.items():
            if k != "CardNamePrefix" and v is not None and v != "":
                rec_to_update[k] = v
        # Generate CardName if missing
        if not rec_to_update.get("CardName"):
            card_name_prefix = updates.get("CardNamePrefix", "")
            if card_name_prefix:
                code = str(rec_to_update.get("CardCode") or f"{idx + 1}")
                rec_to_update["CardName"] = f"{card_name_prefix}{code}".strip()
            elif updates.get("CardName"):
                rec_to_update["CardName"] = updates.get("CardName")
        # Auto-extract PAN from 15-char GSTIN
        fed_id = rec_to_update.get("FederalTaxID") or rec_to_update.get("GSTNo")
        if fed_id and len(str(fed_id).strip()) == 15 and not rec_to_update.get("PANNo"):
            rec_to_update["PANNo"] = str(fed_id).strip()[2:12].upper()
        if fed_id and len(str(fed_id).strip()) == 15 and not rec_to_update.get("GSTNo"):
            rec_to_update["GSTNo"] = str(fed_id).strip().upper()
        norm_rec = normalization_service.normalize_dict(rec_to_update)
        if state.extracted_records and 0 <= idx < len(state.extracted_records):
            state.extracted_records[idx] = norm_rec
        state.normalized_data = norm_rec

    # Re-run bulk validation
    if state.extracted_records:
        bulk_val = validation_service.validate_bulk(state.master_type, state.extracted_records)
        state.bulk_validation = bulk_val

    # Re-validate active record
    val_res = validation_service.validate(state.master_type, state.normalized_data)
    state.validation_result = val_res
    state.missing_fields = val_res.missing_fields

    state.final_payload = val_res.validated_data
    state.missing_fields = []
    state.status = WorkflowStatus.READY_FOR_CONFIRMATION
    state.message = "All records ready. Ready for confirmation."

    AuditService.save_workflow(state)
    return {
        "success": True,
        "status": state.status.value,
        "message": state.message,
        "data": state.model_dump()
    }



