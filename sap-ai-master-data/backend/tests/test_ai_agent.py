"""
Unit tests for Autonomous SAP AI Agent.
Tests universal field updates across Business Partners, Items, and Warehouses,
master data queries, multi-field commands, direct updates, and SHA-256 audit logging.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.sap.client import sap_client
from app.services.audit_service import AuditService


@pytest.fixture(autouse=True)
def ensure_mock_sap(monkeypatch):
    """Ensure tests run in safe simulation mode with fresh seed data."""
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "")
    sap_client._seed_initial_mock_data()


@pytest.mark.asyncio
async def test_agent_query_top_20_business_partners():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/chat", json={
            "message": "Give me top 20 Business Partners"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "QUERY"
        assert data["entity"] == "BusinessPartners"
        assert len(data["records"]) >= 20
        assert any(r.get("CardCode") == "C20000" for r in data["records"])


@pytest.mark.asyncio
async def test_agent_query_items_and_warehouses():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Items query
        res_items = await ac.post("/api/agent/chat", json={"message": "Top 20 Items from SAP"})
        assert res_items.status_code == 200
        data_items = res_items.json()
        assert data_items["success"] is True
        assert data_items["action"] == "QUERY"
        assert data_items["entity"] == "Items"
        assert len(data_items["records"]) >= 20

        # Warehouses query
        res_wh = await ac.post("/api/agent/chat", json={"message": "List all Warehouses"})
        assert res_wh.status_code == 200
        data_wh = res_wh.json()
        assert data_wh["success"] is True
        assert data_wh["action"] == "QUERY"
        assert data_wh["entity"] == "Warehouses"
        assert len(data_wh["records"]) >= 5


@pytest.mark.asyncio
async def test_agent_update_customer_name():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/chat", json={
            "message": "change the customer name which have cardcode C20000 to Cinntra Tech Global"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "UPDATE"
        assert data["entity"] == "BusinessPartners"
        assert data["update_result"]["key"] == "C20000"
        assert data["update_result"]["new_values"]["CardName"] == "Cinntra Tech Global"

        # Verify client mock data updated
        updated_bp = sap_client._mock_records["BusinessPartners"]["C20000"]
        assert updated_bp["CardName"] == "Cinntra Tech Global"


@pytest.mark.asyncio
async def test_agent_update_multi_field_phone_and_email():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/chat", json={
            "message": "update phone of customer C20000 to 9876543210 and email to sales@cinntra.com"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "UPDATE"
        new_vals = data["update_result"]["new_values"]
        assert new_vals["Phone1"] == "9876543210"
        assert new_vals["EmailAddress"] == "sales@cinntra.com"

        # Verify client record
        bp = sap_client._mock_records["BusinessPartners"]["C20000"]
        assert bp["Phone1"] == "9876543210"
        assert bp["EmailAddress"] == "sales@cinntra.com"


@pytest.mark.asyncio
async def test_agent_update_multi_field_phone_and_tax_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/chat", json={
            "message": "change phone to 9876543210 and tax id to 27AABCU9603R1ZM for customer C20000"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "UPDATE"
        new_vals = data["update_result"]["new_values"]
        assert new_vals["Phone1"] == "9876543210"
        assert new_vals["FederalTaxID"] == "27AABCU9603R1ZM"

        # Verify hash was generated
        assert len(data["update_result"]["hash"]) == 64


@pytest.mark.asyncio
async def test_agent_update_item_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/chat", json={
            "message": "update item ITM-001 name to Ultra Fast Precision Bearing and group code to 105"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "UPDATE"
        assert data["entity"] == "Items"
        assert data["update_result"]["key"] == "ITM-001"
        new_vals = data["update_result"]["new_values"]
        assert new_vals["ItemName"] == "Ultra Fast Precision Bearing"
        assert new_vals["ItemsGroupCode"] == 105

        item = sap_client._mock_records["Items"]["ITM-001"]
        assert item["ItemName"] == "Ultra Fast Precision Bearing"
        assert item["ItemsGroupCode"] == 105


@pytest.mark.asyncio
async def test_agent_update_warehouse_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/chat", json={
            "message": "update warehouse 01 city to Bangalore and state to KA"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "UPDATE"
        assert data["entity"] == "Warehouses"
        new_vals = data["update_result"]["new_values"]
        assert new_vals["City"] == "Bangalore"
        assert new_vals["State"] == "KA"

        wh = sap_client._mock_records["Warehouses"]["01"]
        assert wh["City"] == "Bangalore"
        assert wh["State"] == "KA"


@pytest.mark.asyncio
async def test_agent_direct_update_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/agent/update-field", json={
            "entity": "BusinessPartners",
            "key": "C20001",
            "fields": {
                "CardName": "Maxi-Tech Systems Global",
                "Phone1": "+91-9988776655",
                "City": "Hyderabad"
            }
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["action"] == "UPDATE"
        new_vals = data["update_result"]["new_values"]
        assert new_vals["CardName"] == "Maxi-Tech Systems Global"
        assert new_vals["Phone1"] == "+91-9988776655"
        assert new_vals["City"] == "Hyderabad"


@pytest.mark.asyncio
async def test_agent_audit_trail_recorded():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Trigger an update
        await ac.post("/api/agent/chat", json={
            "message": "change name of customer C20000 to Audit Trail Corp"
        })

    # Retrieve audit logs from AuditService
    logs = AuditService.list_audit_logs(limit=10)
    agent_logs = [l for l in logs if l.get("user_identifier") == "ai_agent"]
    assert len(agent_logs) > 0

    latest = agent_logs[0]
    assert latest["action"] == "PATCH_FIELD_UPDATE"
    assert latest["sap_object_id"] == "C20000"
    assert latest["success"] == 1
    # Verify SHA-256 hash length
    assert len(latest["payload_hash"]) == 64


@pytest.mark.asyncio
async def test_agent_item_master_creation_multi_turn_slot_filling():
    """Verify that creating an Item Master preserves the Items entity throughout multi-turn slot-filling and does not switch to Business Partners."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Step 1: User initializes Item Master creation
        res1 = await ac.post("/api/agent/chat", json={
            "message": "Create an Item Master"
        })
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["success"] is True
        assert data1["entity"] == "Items"
        assert data1["action"] == "CREATE_DRAFT"
        assert data1["is_creation_ready"] is False

        # Step 2: User provides ItemCode
        res2 = await ac.post("/api/agent/chat", json={
            "message": "ItemCode is ITM-024",
            "history": [
                {"role": "assistant", "action": data1["action"], "entity": data1["entity"], "creation_draft": data1["creation_draft"], "missing_fields": data1["missing_fields"]}
            ]
        })
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["success"] is True
        assert data2["entity"] == "Items"
        assert data2["action"] == "CREATE_DRAFT"
        assert data2["creation_draft"]["ItemCode"] == "ITM-024"
        assert data2["creation_draft"]["InventoryUOM"] == "PCS"
        assert data2["is_creation_ready"] is False

        # Step 3: User provides ItemName ("ItemName is Eggs")
        res3 = await ac.post("/api/agent/chat", json={
            "message": "ItemName is Eggs",
            "history": [
                {"role": "assistant", "action": data1["action"], "entity": data1["entity"], "creation_draft": data1["creation_draft"], "missing_fields": data1["missing_fields"]},
                {"role": "user", "content": "ItemCode is ITM-024"},
                {"role": "assistant", "action": data2["action"], "entity": data2["entity"], "creation_draft": data2["creation_draft"], "missing_fields": data2["missing_fields"]}
            ]
        })
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["success"] is True
        assert data3["entity"] == "Items"
        assert data3["action"] == "CREATE_READY"
        assert data3["creation_draft"]["ItemCode"] == "ITM-024"
        assert data3["creation_draft"]["ItemName"] == "Eggs"
        assert data3["creation_draft"]["InventoryUOM"] == "PCS"
        assert data3["is_creation_ready"] is True

