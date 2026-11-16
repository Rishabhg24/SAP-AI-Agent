"""
Automated Test Suite for CIRA Natural Language Query & Filter Engine Enhancement.
Tests all prompt categories:
1. Location / Address Filtering
2. Numeric Balance / Account Thresholds (with typo tolerance)
3. Missing / Not Available Field Audits
4. Real-time / Sync Status & Registration Audits
5. Direct integration with AgentService.handle_message and execute_query
"""
import pytest
import asyncio
from app.services.agent_service import AgentService
from app.sap.client import sap_client


@pytest.fixture(autouse=True)
def ensure_mock_sap(monkeypatch):
    """Ensure test suite runs in safe mock simulation mode with seeded master data."""
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "")
    sap_client._seed_initial_mock_data()


@pytest.mark.asyncio
async def test_location_filtering():
    """Test Location / Address filtering prompts."""
    # 1. "give the business partner whose address is delhi"
    res1 = await AgentService.handle_message(
        message="give the business partner whose address is delhi",
        session_id="test-loc-1"
    )
    assert res1["success"] is True
    assert res1["action"] == "QUERY"
    assert res1["entity"] == "BusinessPartners"
    records1 = res1["records"]
    assert len(records1) > 0
    delhi_codes = [r["CardCode"] for r in records1]
    assert "C20000" in delhi_codes
    assert "C20003" in delhi_codes
    assert "V10000" in delhi_codes
    assert "V10002" in delhi_codes
    for r in records1:
        addr_str = f"{r.get('City', '')} {r.get('Address', '')} {r.get('State', '')}".lower()
        assert "delhi" in addr_str or "dl" in addr_str

    # 2. "list customers located in mumbai"
    res2 = await AgentService.handle_message(
        message="list customers located in mumbai",
        session_id="test-loc-2"
    )
    assert res2["success"] is True
    assert res2["action"] == "QUERY"
    records2 = res2["records"]
    assert len(records2) > 0
    for r in records2:
        assert r["CardType"] == "cCustomer"
        addr_str = f"{r.get('City', '')} {r.get('Address', '')} {r.get('State', '')}".lower()
        assert "mumbai" in addr_str

    # 3. "warehouses in delhi"
    res3 = await AgentService.handle_message(
        message="warehouses in delhi",
        session_id="test-loc-3"
    )
    assert res3["success"] is True
    assert res3["action"] == "QUERY"
    assert res3["entity"] == "Warehouses"
    records3 = res3["records"]
    assert len(records3) > 0
    wh_codes = [r["WarehouseCode"] for r in records3]
    assert "WH-MAIN" in wh_codes
    for r in records3:
        addr_str = f"{r.get('City', '')} {r.get('Street', '')} {r.get('State', '')}".lower()
        assert "delhi" in addr_str


@pytest.mark.asyncio
async def test_numeric_balance_thresholds():
    """Test Numeric Balance / Account Thresholds with typo tolerance."""
    # 1. "list all Customer where account balance greater than 1000"
    res1 = await AgentService.handle_message(
        message="list all Customer where account balance greater than 1000",
        session_id="test-num-1"
    )
    assert res1["success"] is True
    assert res1["action"] == "QUERY"
    records1 = res1["records"]
    assert len(records1) > 0
    cust_codes = [r["CardCode"] for r in records1]
    assert "C20000" in cust_codes  # Balance: 4500
    assert "C20002" in cust_codes  # Balance: 12500
    assert "C20003" in cust_codes  # Balance: 1850
    assert "C20001" not in cust_codes  # Balance: 350
    for r in records1:
        assert r["CardType"] == "cCustomer"
        bal = float(r.get("CurrentAccountBalance") or r.get("Balance") or 0)
        assert bal > 1000.0

    # 2. "vendor balance greter than 1000" (Typo tolerance on 'greter')
    res2 = await AgentService.handle_message(
        message="vendor balance greter than 1000",
        session_id="test-num-2"
    )
    assert res2["success"] is True
    assert res2["action"] == "QUERY"
    records2 = res2["records"]
    assert len(records2) > 0
    vendor_codes = [r["CardCode"] for r in records2]
    assert "V10000" in vendor_codes  # Balance: 8400
    assert "V10001" in vendor_codes  # Balance: 2400
    assert "V10002" in vendor_codes  # Balance: 3200
    assert "V10003" not in vendor_codes  # Balance: 450
    for r in records2:
        assert r["CardType"] == "cSupplier"
        bal = float(r.get("CurrentAccountBalance") or r.get("Balance") or 0)
        assert bal > 1000.0

    # 3. "customers with balance less than 500"
    res3 = await AgentService.handle_message(
        message="customers with balance less than 500",
        session_id="test-num-3"
    )
    assert res3["success"] is True
    assert res3["action"] == "QUERY"
    records3 = res3["records"]
    assert len(records3) > 0
    cust_codes_3 = [r["CardCode"] for r in records3]
    assert "C20001" in cust_codes_3  # Balance: 350
    assert "C20000" not in cust_codes_3
    assert "C20002" not in cust_codes_3
    for r in records3:
        assert r["CardType"] == "cCustomer"
        bal = float(r.get("CurrentAccountBalance") or r.get("Balance") or 0)
        assert bal < 500.0

    # 4. "items with price greater than 500"
    res4 = await AgentService.handle_message(
        message="items with price greater than 500",
        session_id="test-num-4"
    )
    assert res4["success"] is True
    assert res4["action"] == "QUERY"
    assert res4["entity"] == "Items"
    records4 = res4["records"]
    assert len(records4) > 0
    for r in records4:
        assert float(r.get("Price", 0)) > 500.0

    # 5. "stock greater than 100"
    res5 = await AgentService.handle_message(
        message="stock greater than 100",
        session_id="test-num-5"
    )
    assert res5["success"] is True
    assert res5["action"] == "QUERY"
    assert res5["entity"] == "Items"
    records5 = res5["records"]
    assert len(records5) > 0
    for r in records5:
        assert float(r.get("QuantityOnStock", 0)) > 100.0


@pytest.mark.asyncio
async def test_missing_field_audits():
    """Test Missing / Not Available field audit queries."""
    # 1. "list all item master data whose HSN not available"
    res1 = await AgentService.handle_message(
        message="list all item master data whose HSN not available",
        session_id="test-miss-1"
    )
    assert res1["success"] is True
    assert res1["action"] == "QUERY"
    assert res1["entity"] == "Items"
    records1 = res1["records"]
    assert len(records1) > 0
    item_codes = [r["ItemCode"] for r in records1]
    assert "ITM-004" in item_codes
    for r in records1:
        hsn = r.get("HSN")
        chap = r.get("ChapterID")
        assert not hsn or str(hsn).strip().lower() in ["", "none", "null", "n/a", "na", "0"]
        assert not chap or str(chap).strip().lower() in ["", "none", "null", "n/a", "na", "0"]

    # 2. "items without HSN code" / "items with missing HSN"
    res2 = await AgentService.handle_message(
        message="items without HSN code",
        session_id="test-miss-2"
    )
    assert res2["success"] is True
    assert res2["action"] == "QUERY"
    assert len(res2["records"]) > 0

    res2_b = await AgentService.handle_message(
        message="items with missing HSN",
        session_id="test-miss-2b"
    )
    assert res2_b["success"] is True
    assert res2_b["action"] == "QUERY"
    assert len(res2_b["records"]) > 0

    # 3. "bp master whose GST Not available"
    res3 = await AgentService.handle_message(
        message="bp master whose GST Not available",
        session_id="test-miss-3"
    )
    assert res3["success"] is True
    assert res3["action"] == "QUERY"
    assert res3["entity"] == "BusinessPartners"
    records3 = res3["records"]
    assert len(records3) > 0
    bp_codes = [r["CardCode"] for r in records3]
    assert "C20003" in bp_codes  # FederalTaxID is 'UNREGISTERED'
    assert "V10002" in bp_codes  # FederalTaxID is None
    assert "V10003" in bp_codes  # FederalTaxID is 'URP'
    for r in records3:
        tax_id = r.get("FederalTaxID")
        assert not tax_id or str(tax_id).strip().upper() in ["", "NONE", "NULL", "UNREGISTERED", "URP", "N/A", "NA"]


@pytest.mark.asyncio
async def test_realtime_and_sync_audits():
    """Test Real-time / Sync Status & Registration Audits."""
    # 1. "bp master whose GST Not available or not in realtime SAP" (Composite OR condition)
    res1 = await AgentService.handle_message(
        message="bp master whose GST Not available or not in realtime SAP",
        session_id="test-sync-1"
    )
    assert res1["success"] is True
    assert res1["action"] == "QUERY"
    assert res1["entity"] == "BusinessPartners"
    records1 = res1["records"]
    assert len(records1) > 0
    bp_codes = [r["CardCode"] for r in records1]
    assert "C20003" in bp_codes
    assert "V10002" in bp_codes

    # 2. "unregistered business partners"
    res2 = await AgentService.handle_message(
        message="unregistered business partners",
        session_id="test-sync-2"
    )
    assert res2["success"] is True
    assert res2["action"] == "QUERY"
    assert res2["entity"] == "BusinessPartners"
    records2 = res2["records"]
    assert len(records2) > 0
    bp_codes_2 = [r["CardCode"] for r in records2]
    assert "C20003" in bp_codes_2 or "V10002" in bp_codes_2

    # 3. "drafts not synced to SAP"
    res3 = await AgentService.handle_message(
        message="drafts not synced to SAP",
        session_id="test-sync-3"
    )
    assert res3["success"] is True
    assert res3["action"] == "QUERY"
    records3 = res3["records"]
    assert len(records3) > 0


@pytest.mark.asyncio
async def test_intent_detection_precision():
    """Verify detect_intent correctly classifies query filter prompts vs creation/update/health."""
    # Condition queries must be QUERY
    assert AgentService.detect_intent("give the business partner whose address is delhi") == "QUERY"
    assert AgentService.detect_intent("list customers located in mumbai") == "QUERY"
    assert AgentService.detect_intent("warehouses in delhi") == "QUERY"
    assert AgentService.detect_intent("list all Customer where account balance greater than 1000") == "QUERY"
    assert AgentService.detect_intent("vendor balance greter than 1000") == "QUERY"
    assert AgentService.detect_intent("customers with balance less than 500") == "QUERY"
    assert AgentService.detect_intent("items with price greater than 500") == "QUERY"
    assert AgentService.detect_intent("stock greater than 100") == "QUERY"
    assert AgentService.detect_intent("list all item master data whose HSN not available") == "QUERY"
    assert AgentService.detect_intent("items without HSN code") == "QUERY"
    assert AgentService.detect_intent("items with missing HSN") == "QUERY"
    assert AgentService.detect_intent("bp master whose GST Not available") == "QUERY"
    assert AgentService.detect_intent("bp master whose GST Not available or not in realtime SAP") == "QUERY"
    assert AgentService.detect_intent("unregistered business partners") == "QUERY"
    assert AgentService.detect_intent("drafts not synced to SAP") == "QUERY"

    # Specific attribute queries must remain SPECIFIC_QUERY
    assert AgentService.detect_intent("What is the address of customer C20000?") == "SPECIFIC_QUERY"
    assert AgentService.detect_intent("What is the tax rate of item ITM-001?") == "SPECIFIC_QUERY"

    # Health and Creation
    assert AgentService.detect_intent("sap health") == "HEALTH"
    assert AgentService.detect_intent("Create a Business Partner") == "CREATE"
    assert AgentService.detect_intent("change phone to 9876543210 for customer C20000") == "UPDATE"
