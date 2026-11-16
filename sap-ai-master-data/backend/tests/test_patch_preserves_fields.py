import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import asyncio
from app.config import settings
from app.sap.client import sap_client
from app.agent.tools import execute_field_update


def setup_module():
    # Ensure offline test deterministic environment
    settings.sap_service_layer_url = ""


@pytest.mark.asyncio
async def test_patch_preserves_all_bp_fields():
    """
    Verify that updating a single field (like Phone1) via PATCH on BusinessPartners
    NEVER strips or removes any existing master data details.
    """
    settings.sap_service_layer_url = ""
    # Ensure C20000 is seeded in mock store
    sap_client._seed_initial_mock_data()
    original_record = await sap_client.get("BusinessPartners", key="C20000")
    assert original_record is not None
    assert original_record.get("CardName") == "Cinntra Infotech Solutions"
    assert original_record.get("FederalTaxID") == "07AABCU9603R1ZM"
    assert original_record.get("City") == "Delhi"

    # Execute PATCH update with ONLY Phone1 in payload
    result = await execute_field_update(
        entity="BusinessPartners",
        key="C20000",
        fields={"Phone1": "7505576998"},
        prompt="change phone to 7505576998 for customer C20000"
    )

    assert result["success"] is True
    records = result.get("records", [])
    assert len(records) == 1
    patched = records[0]

    # Verify updated field
    assert patched.get("Phone1") == "7505576998"

    # Verify ALL original fields are preserved and NOT removed/empty
    assert patched.get("CardCode") == "C20000"
    assert patched.get("CardName") == "Cinntra Infotech Solutions"
    assert patched.get("CardType") == "cCustomer"
    assert patched.get("FederalTaxID") == "07AABCU9603R1ZM"
    assert patched.get("City") == "Delhi"
    assert patched.get("Address") == "Connaught Place, Central Delhi"
    assert patched.get("CreateDate") == "2026-08-15"
    assert patched.get("CurrentAccountBalance") == 4500.0


@pytest.mark.asyncio
async def test_sap_client_patch_preserves_all_fields():
    """
    Verify that sap_client.patch directly returns a fully hydrated record
    preserving existing master data rather than returning only the new payload.
    """
    settings.sap_service_layer_url = ""
    sap_client._seed_initial_mock_data()

    res = await sap_client.patch(
        entity="BusinessPartners",
        key="C20000",
        payload={"Phone1": "9998887776"}
    )

    assert res.get("Phone1") == "9998887776"
    assert res.get("CardCode") == "C20000"
    assert res.get("CardName") == "Cinntra Infotech Solutions"
    assert res.get("FederalTaxID") == "07AABCU9603R1ZM"
    assert res.get("City") == "Delhi"


@pytest.mark.asyncio
async def test_patch_item_preserves_all_fields():
    """
    Verify that updating Item fields via PATCH preserves ItemCode, ItemName, Group, etc.
    """
    settings.sap_service_layer_url = ""
    sap_client._seed_initial_mock_data()

    result = await execute_field_update(
        entity="Items",
        key="ITM-001",
        fields={"Price": 599.0},
        prompt="update price to 599 for item ITM-001"
    )

    assert result["success"] is True
    patched = result["records"][0]
    assert patched.get("Price") == 599.0
    assert patched.get("ItemCode") == "ITM-001"
    assert patched.get("ItemName") == "Industrial Deep Groove Ball Bearing 6205"
    assert patched.get("ItemsGroupCode") == 100


if __name__ == "__main__":
    asyncio.run(test_patch_preserves_all_bp_fields())
    asyncio.run(test_sap_client_patch_preserves_all_fields())
    asyncio.run(test_patch_item_preserves_all_fields())
    print("\nALL PATCH PRESERVATION TESTS PASSED SUCCESSFULLY!")
