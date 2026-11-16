"""
Unit tests for conversational missing-field collection via /api/chat.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.models.extraction import MasterDataType
from app.models.workflow import WorkflowState, WorkflowStatus
from app.services.audit_service import AuditService

@pytest.mark.asyncio
async def test_chat_asks_and_collects_missing_mandatory_fields():
    wf_id = "test-chat-missing-fields-wf"
    # Item with only ItemCode and ItemName provided (missing TaxRate, HSN, etc.)
    partial_item = {
        "ItemCode": "ITM-CHAT-01",
        "ItemName": "Chat Collection Test Bolt",
        "ItemsGroupCode": 100,
        "InventoryUOM": "PCS",
        "ItemType": "Inventory/Sales/Purchase",
        # Missing TaxRate, ItemManagementMethod, ItemCategory, MaterialType, HSN, TaxCategory
    }
    from app.services.validation_service import validation_service
    val_res = validation_service.validate(MasterDataType.ITEM, partial_item)
    assert not val_res.valid
    assert len(val_res.missing_fields) > 0

    state = WorkflowState(
        workflow_id=wf_id,
        master_type=MasterDataType.ITEM,
        status=WorkflowStatus.MISSING_FIELDS,
        normalized_data=partial_item,
        missing_fields=val_res.missing_fields,
        validation_result=val_res
    )
    AuditService.save_workflow(state)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First test: User provides TaxRate
        res = await ac.post("/api/chat", json={
            "workflow_id": wf_id,
            "message": "TaxRate: 18%"
        })
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["workflow_id"] == wf_id
        assert data["extracted_updates"]["TaxRate"] == 18.0 or data["extracted_updates"]["TaxRate"] == "18" or data["extracted_updates"]["TaxRate"] == 18

        # Verify state in DB updated with TaxRate
        updated_state = AuditService.get_workflow(wf_id)
        assert updated_state is not None
        assert "TaxRate" in updated_state.normalized_data

        # Now provide the rest of the missing fields:
        missing_fields = updated_state.missing_fields
        field_values = {
            "ItemManagementMethod": "Batch",
            "ItemCategory": "Item",
            "MaterialType": "RM",
            "HSN": "73181500",
            "TaxCategory": "Taxable"
        }
        for mf in missing_fields:
            fname = mf.field if hasattr(mf, "field") else mf.get("field")
            if fname in field_values:
                ans_res = await ac.post("/api/chat", json={
                    "workflow_id": wf_id,
                    "message": f"{fname}: {field_values[fname]}"
                })
                assert ans_res.status_code == 200

        # After all mandatory fields are provided, workflow is READY_FOR_CONFIRMATION
        final_state = AuditService.get_workflow(wf_id)
        assert final_state.status == WorkflowStatus.READY_FOR_CONFIRMATION
        assert len(final_state.missing_fields) == 0
