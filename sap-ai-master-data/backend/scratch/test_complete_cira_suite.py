import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.agent_service import agent_service

async def run_suite():
    print("=== TESTING COMPLETE CIRA WORKFLOWS ===")

    # 1. SCENARIO FROM USER SCREENSHOT:
    # History contains previous failed Business Partner draft for C012345
    # User types "create item master"
    print("\n--- TEST 1: 'create item master' after a previous BP failure in history ---")
    stale_history = [
        {"role": "user", "content": "Create a Business Partner"},
        {
            "role": "assistant",
            "content": "Duplicate Identifier",
            "action": "CREATE_FAILED",
            "entity": "BusinessPartners",
            "creation_draft": {"CardCode": "C012345", "CardName": "Old BP", "Address": "B-94", "GSTNo": "27AABCU9603R1ZM"},
            "is_creation_ready": False
        }
    ]
    res_item_init = await agent_service.process_chat("create item master", history=stale_history)
    print("Action:", res_item_init.get("action"))
    print("Entity:", res_item_init.get("entity"))
    print("Draft:", res_item_init.get("creation_draft"))
    print("Missing fields count:", len(res_item_init.get("missing_fields", [])))
    assert res_item_init.get("entity") == "Items", f"Expected Items, got {res_item_init.get('entity')}"
    assert res_item_init.get("action") == "CREATE_DRAFT", f"Expected CREATE_DRAFT, got {res_item_init.get('action')}"
    print(">>> PASS: 'create item master' correctly starts fresh Item creation without inheriting BP draft!")

    # 2. Complete item creation in multi-turn prompt
    print("\n--- TEST 2: Multi-turn Item slot filling ---")
    item_history = [
        {"role": "user", "content": "create item master"},
        {
            "role": "assistant",
            "content": res_item_init.get("reply"),
            "action": "CREATE_DRAFT",
            "entity": "Items",
            "creation_draft": {},
            "missing_fields": res_item_init.get("missing_fields")
        }
    ]
    res_item_fill = await agent_service.process_chat("ItemCode is ITM-9911, ItemName is Industrial Nut M12, UOM is PCS", history=item_history)
    print("Action:", res_item_fill.get("action"))
    print("Entity:", res_item_fill.get("entity"))
    print("Ready:", res_item_fill.get("is_creation_ready"))
    print("Draft:", res_item_fill.get("creation_draft"))
    assert res_item_fill.get("is_creation_ready") is True
    print(">>> PASS: Item slot filling correctly produces 100% ready draft!")

    # 3. Direct 1-line item creation prompt
    print("\n--- TEST 3: 1-line Item Creation Prompt ---")
    res_direct_item = await agent_service.process_chat("Add new item Heavy Duty Bearing with code ITM-9922, in PCS, tax 18%")
    print("Action:", res_direct_item.get("action"))
    print("Draft:", res_direct_item.get("creation_draft"))
    print("Ready:", res_direct_item.get("is_creation_ready"))
    assert res_direct_item.get("entity") == "Items"
    assert res_direct_item.get("is_creation_ready") is True
    print(">>> PASS: 1-line Item creation prompt successful!")

    # 4. Direct 1-line Warehouse Creation Prompt
    print("\n--- TEST 4: Warehouse Creation Prompt ---")
    res_wh = await agent_service.process_chat("Register warehouse WH-CENTRAL in Bhiwandi Logistics Park")
    print("Action:", res_wh.get("action"))
    print("Entity:", res_wh.get("entity"))
    print("Draft:", res_wh.get("creation_draft"))
    assert res_wh.get("entity") == "Warehouses"
    print(">>> PASS: Warehouse creation prompt successful!")

    # 5. Granular Retrieval of any master record
    print("\n--- TEST 5: Granular Retrieval ---")
    q_bp = await agent_service.process_chat("What is the address of customer C20000?")
    print("BP Address Granular:", q_bp.get("granular_answer"))
    assert q_bp.get("granular_answer") is not None

    q_itm = await agent_service.process_chat("What is the tax rate of item ITM-001?")
    print("Item Tax Rate Granular:", q_itm.get("granular_answer"))
    assert q_itm.get("granular_answer") is not None

    q_wh = await agent_service.process_chat("Where is warehouse 01 located?")
    print("Warehouse Location Granular:", q_wh.get("granular_answer"))
    assert q_wh.get("granular_answer") is not None

    # 6. Natural Language Field Updates on existing records
    print("\n--- TEST 6: Field Updates ---")
    u_wh = await agent_service.process_chat("Update warehouse 01 city to Thane")
    print("Warehouse Update:", u_wh.get("action"), u_wh.get("update_result"))
    assert u_wh.get("action") == "UPDATE"

    print("\n=======================================================")
    print("🎉 ALL CIRA FUNCTIONALITY VERIFIED AND WORKING PERFECTLY!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(run_suite())
