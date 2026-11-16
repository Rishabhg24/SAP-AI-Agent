import pytest
from app.models.extraction import MasterDataType
from app.services.validation_service import validation_service
from app.models.workflow import WorkflowState, WorkflowStatus
from app.services.audit_service import AuditService
from httpx import AsyncClient, ASGITransport
from app.main import app

def test_validate_bulk_items():
    records = [
        {
            "ItemCode": f"ITM-{i}",
            "ItemName": f"Item {i}",
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
        for i in range(10)
    ]
    summary = validation_service.validate_bulk(MasterDataType.ITEM, records)
    assert summary.total == 10
    assert summary.valid_count == 10
    assert summary.invalid_count == 0
    assert len(summary.record_statuses) == 10

def test_validate_bulk_bp_with_missing_fields():
    # Only CardCode and FederalTaxID provided
    records = [
        {"CardCode": f"C{i:05d}", "FederalTaxID": "10ABCDE1234F1Z5"}
        for i in range(5)
    ]
    summary = validation_service.validate_bulk(MasterDataType.BUSINESS_PARTNER, records)
    assert summary.total == 5
    assert summary.valid_count == 0
    assert summary.invalid_count == 5
    assert "CardName" in summary.missing_fields_summary
    assert "Address" in summary.missing_fields_summary

@pytest.mark.asyncio
async def test_bulk_apply_defaults_and_confirm(respx_mock):
    wf_id = "test-bulk-wf-1"
    raw_records = [
        {"CardCode": "C001", "FederalTaxID": "10ABCDE1234F1Z5"},
        {"CardCode": "C002", "FederalTaxID": "09BCDEF2345G1Z6"}
    ]
    state = WorkflowState(
        workflow_id=wf_id,
        master_type=MasterDataType.BUSINESS_PARTNER,
        status=WorkflowStatus.MISSING_FIELDS,
        normalized_data=raw_records[0],
        extracted_records=raw_records,
        total_records=2
    )
    AuditService.save_workflow(state)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Apply defaults for all mandatory fields
        resp = await ac.post(f"/api/workflows/{wf_id}/bulk-apply-defaults", json={
            "defaults": {
                "CardType": "Customer",
                "CardNamePrefix": "Client ",
                "Address": "100 Silicon Way, San Jose, CA",
                "TaxDetails": "GST 18%",
                "PaymentTerms": "Net 30",
                "Currency": "INR",
                "ControlAccount": "211000",
                "GSTNo": "27AABCU9603R1ZM",
                "PANNo": "AABCU9603R"
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["bulk_validation"]["valid_count"] == 2

        # Bulk confirm
        conf_resp = await ac.post(f"/api/master-data/{wf_id}/bulk-confirm", json={"confirmed": True})
        assert conf_resp.status_code == 200
        assert conf_resp.json()["data"]["is_confirmed"] is True

@pytest.mark.asyncio
async def test_bulk_create_endpoint_with_mock_sap():
    from unittest.mock import patch
    wf_id = "test-bulk-wf-items"
    records = [
        {
            "ItemCode": f"BLK-ITM-{i}",
            "ItemName": f"Bulk Item {i}",
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
        for i in range(3)
    ]
    state = WorkflowState(
        workflow_id=wf_id,
        master_type=MasterDataType.ITEM,
        status=WorkflowStatus.CONFIRMED,
        is_confirmed=True,
        normalized_data=records[0],
        extracted_records=records,
        total_records=3
    )
    AuditService.save_workflow(state)

    with patch("app.sap.items.SAPItemsService.check_item_exists", return_value=False), \
         patch("app.sap.items.SAPItemsService.create_item", side_effect=lambda m: {"ItemCode": m.ItemCode}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(f"/api/master-data/{wf_id}/bulk-create", json={
                "skip_duplicates": True,
                "continue_on_error": True
            })
            assert resp.status_code == 200
            res = resp.json()
            assert res["success"] is True
            assert res["data"]["summary"]["total_submitted"] == 3
            assert res["data"]["summary"]["created_count"] == 3
            assert len(res["data"]["summary"]["records"]) == 3

@pytest.mark.asyncio
async def test_bulk_create_direct_endpoint():
    from unittest.mock import patch
    direct_records = [
        {
            "ItemCode": f"DIR-ITM-{i}",
            "ItemName": f"Direct Item {i}",
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
        for i in range(4)
    ]
    with patch("app.sap.items.SAPItemsService.check_item_exists", return_value=False), \
         patch("app.sap.items.SAPItemsService.create_item", side_effect=lambda m: {"ItemCode": m.ItemCode}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/master-data/bulk-create-direct", json={
                "master_type": "item",
                "records": direct_records,
                "skip_duplicates": True,
                "continue_on_error": True,
                "confirmed": True
            })
            assert resp.status_code == 200
            res = resp.json()
            assert res["success"] is True
            assert res["data"]["summary"]["total_submitted"] == 4
            assert res["data"]["summary"]["created_count"] == 4
            assert len(res["data"]["summary"]["records"]) == 4
