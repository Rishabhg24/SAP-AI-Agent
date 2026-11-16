import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from app.services.agent_service import AgentService
from app.sap.client import sap_client


@pytest.fixture(autouse=True)
def ensure_mock_sap(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "")
    sap_client._seed_initial_mock_data()


@pytest.mark.asyncio
async def test():
    print("--- Test 1: Typing 'change the addes of Customer C20000' with prior item creation in history ---")
    history_after_item = [
        {"role": "user", "content": "Create an Item Master with code ITM-098 and name Eggs"},
        {"role": "assistant", "action": "CREATE_READY", "entity": "Items", "creation_draft": {"ItemCode": "ITM-098", "InventoryUOM": "PCS", "ItemName": "Eggs"}, "is_creation_ready": True},
    ]

    res1 = await AgentService.process_chat("change the addes of Customer C20000", history=history_after_item)
    print("Turn 1 Action:", res1.get("action"))
    print("Turn 1 Entity:", res1.get("entity"))
    print("Turn 1 Target Key:", res1.get("target_key"))
    print("Turn 1 Target Field:", res1.get("target_field"))
    print("Turn 1 Creation Draft:", res1.get("creation_draft"))
    assert res1.get("action") == "UPDATE"
    assert res1.get("entity") == "BusinessPartners"
    assert res1.get("target_key") == "C20000"
    assert res1.get("target_field") == "Address"
    assert res1.get("creation_draft") is None

    print("\n--- Test 2: User responds with 'city' ---")
    history_after_addes = [
        *history_after_item,
        {"role": "user", "content": "change the addes of Customer C20000"},
        {"role": "assistant", "action": res1.get("action"), "entity": res1.get("entity"), "target_key": res1.get("target_key"), "target_field": res1.get("target_field"), "reply": res1.get("reply")}
    ]

    res2 = await AgentService.process_chat("city", history=history_after_addes)
    print("Turn 2 Action:", res2.get("action"))
    print("Turn 2 Entity:", res2.get("entity"))
    print("Turn 2 Target Key:", res2.get("target_key"))
    print("Turn 2 Target Field:", res2.get("target_field"))
    print("Turn 2 Creation Draft:", res2.get("creation_draft"))
    assert res2.get("action") == "UPDATE"
    assert res2.get("entity") == "BusinessPartners"
    assert res2.get("target_key") == "C20000"
    assert res2.get("target_field") == "City"
    assert res2.get("creation_draft") is None

    print("\n--- Test 3: User responds with 'Mumbai' (or 'city to Mumbai') ---")
    history_after_city = [
        *history_after_addes,
        {"role": "user", "content": "city"},
        {"role": "assistant", "action": res2.get("action"), "entity": res2.get("entity"), "target_key": res2.get("target_key"), "target_field": res2.get("target_field"), "reply": res2.get("reply")}
    ]

    res3 = await AgentService.process_chat("Mumbai", history=history_after_city)
    print("Turn 3 Action:", res3.get("action"))
    print("Turn 3 Entity:", res3.get("entity"))
    print("Turn 3 Update Result:", res3.get("update_result"))
    assert res3.get("action") == "UPDATE"
    assert res3.get("entity") == "BusinessPartners"
    assert res3.get("update_result") is not None
    assert res3.get("update_result", {}).get("key") == "C20000"
    assert "City" in res3.get("update_result", {}).get("updated_fields", {})

    print("\n--- Test 4: Single-turn 'change the addes of Customer C20000 to Sector 62, Noida' ---")
    res4 = await AgentService.process_chat("change the addes of Customer C20000 to Sector 62, Noida", history=history_after_item)
    print("Turn 4 Action:", res4.get("action"))
    print("Turn 4 Entity:", res4.get("entity"))
    print("Turn 4 Update Result:", res4.get("update_result"))
    assert res4.get("action") == "UPDATE"
    assert res4.get("entity") == "BusinessPartners"
    assert res4.get("update_result") is not None
    assert res4.get("update_result", {}).get("key") == "C20000"
    assert "Address" in res4.get("update_result", {}).get("updated_fields", {})

    print("\nALL 4 TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(test())
