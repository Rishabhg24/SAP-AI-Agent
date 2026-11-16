"""
End-to-End Workflow and Audit Tests using FastAPI TestClient / AsyncClient.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.models.extraction import MasterDataType
from app.models.workflow import WorkflowState, WorkflowStatus
from app.services.audit_service import AuditService

@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["status"] == "HEALTHY"

        sap_res = await ac.get("/api/sap/health")
        assert sap_res.status_code == 200
        sap_data = sap_res.json()
        assert "status" in sap_data

@pytest.mark.asyncio
async def test_confirmation_gate_prevents_unconfirmed_posting(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create unconfirmed workflow state
        wf_id = "test-unconfirmed-wf-001"
        full_item = {
            "ItemCode": "ITM-GATE-1",
            "ItemName": "Gate Test Item",
            "ItemsGroupCode": 100,
            "InventoryUOM": "PCS",
            "ItemType": "Inventory/Sales/Purchase",
            "TaxRate": "18%",
            "ItemManagementMethod": "None",
            "ItemCategory": "Item",
            "MaterialType": "RM",
            "HSN": "73181500",
            "TaxCategory": "Taxable"
        }
        wf_state = WorkflowState(
            workflow_id=wf_id,
            master_type=MasterDataType.ITEM,
            status=WorkflowStatus.READY_FOR_CONFIRMATION,
            is_confirmed=False,
            normalized_data=full_item,
            final_payload=full_item
        )
        AuditService.save_workflow(wf_state)

        # Attempt to create in SAP without confirmation
        create_res = await ac.post("/api/master-data/item/create", json={"workflow_id": wf_id})
        assert create_res.status_code == 400
        assert "Explicit user confirmation is required" in create_res.json()["detail"]

        # Now explicitly confirm
        confirm_res = await ac.post(f"/api/master-data/{wf_id}/confirm", json={"confirmed": True})
        assert confirm_res.status_code == 200
        assert confirm_res.json()["data"]["is_confirmed"] is True

        # Now creation should succeed
        final_create = await ac.post("/api/master-data/item/create", json={"workflow_id": wf_id})
        assert final_create.status_code == 200
        assert final_create.json()["success"] is True
        assert final_create.json()["status"] == "CREATED"

        # Verify audit record exists
        audit_res = await ac.get("/api/audit/logs?limit=5")
        assert audit_res.status_code == 200
        logs = audit_res.json()["data"]
        assert any(l["workflow_id"] == wf_id for l in logs)
