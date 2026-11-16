"""
Comprehensive verification test for advanced autonomous SAP AI agent.
Tests:
- Prompt-driven Business Partner creation & validation
- Prompt-driven Item Master creation & validation
- Prompt-driven Warehouse creation & validation
- Direct & multi-turn slot filling
- Prompt-based posting to SAP
- Granular retrieval for Business Partners, Items, and Warehouses (e.g. address of ABC)
"""
import pytest
import asyncio
import time
from app.services.agent_service import agent_service
from app.sap.client import sap_client


@pytest.fixture(autouse=True)
def ensure_mock_sap(monkeypatch):
    """Ensure tests run in safe simulation mode with fresh seed data."""
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "")
    sap_client._seed_initial_mock_data()


@pytest.mark.asyncio
async def test_business_partner_creation_multi_turn():
    test_code = f"C{int(time.time()) % 80000 + 10000}"
    # Turn 1: User says "create a business partner"
    res1 = await agent_service.process_chat("create a business partner")
    assert res1["action"] == "CREATE_DRAFT"
    assert res1["entity"] == "BusinessPartners"
    assert len(res1["missing_fields"]) > 0
    assert not res1["is_creation_ready"]

    # Turn 2: User provides CardCode and CardName
    history1 = [
        {"role": "user", "content": "create a business partner"},
        {"role": "assistant", "action": res1["action"], "entity": res1["entity"], "creation_draft": res1["creation_draft"], "missing_fields": res1["missing_fields"]}
    ]
    res2 = await agent_service.process_chat(f"CardCode is {test_code} and name is Apex Precision Ltd", history=history1)
    assert res2["action"] == "CREATE_DRAFT"
    assert res2["creation_draft"]["CardCode"] == test_code
    assert res2["creation_draft"]["CardName"] == "Apex Precision Ltd"

    # Turn 3: User provides Address and GSTIN (GSTIN auto-derives PAN)
    history2 = [
        *history1,
        {"role": "user", "content": f"CardCode is {test_code} and name is Apex Precision Ltd"},
        {"role": "assistant", "action": res2["action"], "entity": res2["entity"], "creation_draft": res2["creation_draft"], "missing_fields": res2["missing_fields"]}
    ]
    res3 = await agent_service.process_chat("Address is 100 Industrial Zone, Mumbai, GST is 27AAACG0568M1Z2", history=history2)
    assert res3["action"] == "CREATE_READY"
    assert res3["is_creation_ready"] is True
    assert res3["creation_draft"]["PANNo"] == "AAACG0568M"
    assert res3["creation_draft"]["GSTNo"] == "27AAACG0568M1Z2"

    # Turn 4: User confirms creation via prompt
    history3 = [
        *history2,
        {"role": "user", "content": "Address is 100 Industrial Zone, Mumbai, GST is 27AAACG0568M1Z2"},
        {"role": "assistant", "action": res3["action"], "entity": res3["entity"], "creation_draft": res3["creation_draft"], "is_creation_ready": True}
    ]
    res4 = await agent_service.process_chat("post to sap", history=history3)
    assert res4["action"] == "CREATE_SUCCESS"
    assert res4["success"] is True
    assert len(res4["records"]) == 1
    assert res4["records"][0]["CardCode"] == test_code


@pytest.mark.asyncio
async def test_item_master_creation_and_post():
    test_icode = f"ITM-{int(time.time()) % 80000 + 10000}"
    # Create item in one comprehensive prompt
    prompt = f"Create new item with ItemCode {test_icode}, ItemName Ultra Heavy Bolt M12, TaxRate 18%, UOM PCS, HSN 73181500, Group 100"
    res = await agent_service.process_chat(prompt)
    assert res["action"] == "CREATE_READY"
    assert res["is_creation_ready"] is True
    assert res["creation_draft"]["ItemCode"] == test_icode
    assert res["creation_draft"]["ItemName"] == "Ultra Heavy Bolt M12"

    # Post by typing "confirm"
    history = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "action": res["action"], "entity": res["entity"], "creation_draft": res["creation_draft"], "is_creation_ready": True}
    ]
    post_res = await agent_service.process_chat("confirm", history=history)
    assert post_res["action"] == "CREATE_SUCCESS"
    assert post_res["success"] is True
    assert post_res["records"][0]["ItemCode"] == test_icode


@pytest.mark.asyncio
async def test_warehouse_creation_and_post():
    test_wh = f"W{int(time.time()) % 8000 + 1000}"
    prompt = f"Create warehouse with WarehouseCode {test_wh}, WarehouseName South Storage Terminal, Location 1, Address 42 Harbor Drive, Chennai"
    res = await agent_service.process_chat(prompt)
    assert res["action"] == "CREATE_READY"
    assert res["is_creation_ready"] is True
    assert res["creation_draft"]["WarehouseCode"] == test_wh
    assert res["creation_draft"]["WarehouseName"] == "South Storage Terminal"

    # Post to SAP
    history = [
        {"role": "user", "content": prompt},
        {"role": "assistant", "action": res["action"], "entity": res["entity"], "creation_draft": res["creation_draft"], "is_creation_ready": True}
    ]
    post_res = await agent_service.process_chat("yes please create it", history=history)
    assert post_res["action"] == "CREATE_SUCCESS"
    assert post_res["success"] is True
    assert post_res["records"][0]["WarehouseCode"] == test_wh


@pytest.mark.asyncio
async def test_granular_attribute_retrieval():
    # 1. Address of Business Partner by code
    res_addr = await agent_service.process_chat("What is the address of customer C20000?")
    assert res_addr["success"] is True
    assert res_addr["granular_answer"] is not None
    assert any(loc in res_addr["granular_answer"]["value"] for loc in ["Delhi", "Mumbai"])

    # 2. Address of Business Partner by Name
    res_name = await agent_service.process_chat("What is the address of Cinntra Infotech Solutions?")
    assert res_name["success"] is True
    assert res_name["granular_answer"] is not None
    assert any(loc in res_name["granular_answer"]["value"] for loc in ["NOIDA", "Mumbai", "201301", "Delhi", "Connaught Place"])

    # 3. Phone number of Business Partner
    res_phone = await agent_service.process_chat("What is the phone number of customer C20000?")
    assert res_phone["success"] is True
    assert res_phone["granular_answer"] is not None
    assert "Phone" in res_phone["granular_answer"]["attribute"]

    # 4. Tax rate of item
    res_tax = await agent_service.process_chat("What is the tax rate of item ITM-001?")
    assert res_tax["success"] is True
    assert res_tax["granular_answer"] is not None
    assert "Tax" in res_tax["granular_answer"]["attribute"]

    # 5. Warehouse location query
    res_wh = await agent_service.process_chat("Where is warehouse WH01 located?")
    assert res_wh["success"] is True
    assert res_wh["granular_answer"] is not None
