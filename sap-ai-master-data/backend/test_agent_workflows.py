import asyncio
import sys
from app.services.agent_service import agent_service

async def test_all_agent_workflows():
    print("=== TESTING HEY CIRA AGENT WORKFLOWS ===")
    
    # 1. Test Isolation: 'create item master' with previous failed BP draft in history
    print("\n--- TEST 1: Creation Isolation ('create item master' with old BP draft in history) ---")
    bp_history = [
        {"role": "user", "content": "Create BP C012345"},
        {"role": "assistant", "content": "Duplicate Identifier", "creation_draft": {"CardCode": "C012345", "CardName": "Old BP", "Address": "B-94", "GSTNo": "27AABCU9603R1ZM"}, "action": "CREATE_FAILED", "entity": "BusinessPartners"}
    ]
    res_iso = await agent_service.process_chat("create item master", history=bp_history)
    print("Action:", res_iso.get("action"))
    print("Entity:", res_iso.get("entity"))
    print("Missing fields:", [m["field"] for m in res_iso.get("missing_fields", [])])
    assert res_iso.get("action") == "CREATE_DRAFT", f"Expected CREATE_DRAFT, got {res_iso.get('action')}"
    assert res_iso.get("entity") == "Items", f"Expected Items, got {res_iso.get('entity')}"
    assert "C012345" not in str(res_iso.get("creation_draft")), "Old BP draft leaked into Item Master creation!"
    print("[OK] Test 1 Passed: Isolation verified, no draft leakage!")

    # 2. Test Step-by-Step Item Master Creation
    print("\n--- TEST 2: Item Master Slot Filling ---")
    turn1 = await agent_service.process_chat("create an item master")
    assert turn1.get("entity") == "Items"
    assert turn1.get("action") == "CREATE_DRAFT"
    
    history_itm = [
        {"role": "user", "content": "create an item master"},
        {"role": "assistant", "content": turn1.get("reply"), "creation_draft": turn1.get("creation_draft"), "missing_fields": turn1.get("missing_fields"), "action": "CREATE_DRAFT", "entity": "Items"}
    ]
    turn2 = await agent_service.process_chat("ItemCode is ITM-9988, ItemName is High Tensile Hex Bolt M12, UOM is PCS", history=history_itm)
    print("Turn 2 Action:", turn2.get("action"))
    print("Turn 2 Draft:", turn2.get("creation_draft"))
    print("Turn 2 Ready:", turn2.get("is_creation_ready"))
    assert turn2.get("is_creation_ready") == True, "Item Master should be ready for SAP posting"
    assert turn2.get("action") == "CREATE_READY"
    print("[OK] Test 2 Passed: Item Master multi-turn slot filling complete!")

    # 3. Test Single-Prompt Item Master Creation
    print("\n--- TEST 3: Item Master Single Prompt Creation ---")
    res_itm = await agent_service.process_chat("Add new Item Bolt M12 with code ITM-7788, UOM PCS, tax 18%")
    print("Action:", res_itm.get("action"), "Entity:", res_itm.get("entity"))
    print("Draft:", res_itm.get("creation_draft"), "Ready:", res_itm.get("is_creation_ready"))
    assert res_itm.get("entity") == "Items"
    assert res_itm.get("creation_draft", {}).get("ItemCode") == "ITM-7788"
    print("[OK] Test 3 Passed: Item Master single prompt parsed accurately!")

    # 4. Test Business Partner Creation
    print("\n--- TEST 4: Business Partner Creation ---")
    res_bp = await agent_service.process_chat("Create a customer called Apex Global in Mumbai with GST 27AABCU9603R1ZM")
    print("Action:", res_bp.get("action"), "Entity:", res_bp.get("entity"))
    print("Draft:", res_bp.get("creation_draft"))
    assert res_bp.get("entity") == "BusinessPartners"
    assert res_bp.get("creation_draft", {}).get("GSTNo") == "27AABCU9603R1ZM"
    assert res_bp.get("creation_draft", {}).get("PANNo") == "AABCU9603R"
    print("[OK] Test 4 Passed: BP parsed with auto-derived PAN!")

    # 5. Test Warehouse Creation
    print("\n--- TEST 5: Warehouse Creation ---")
    res_wh = await agent_service.process_chat("Register warehouse WH-NORTH in Gurgaon")
    print("Action:", res_wh.get("action"), "Entity:", res_wh.get("entity"))
    print("Draft:", res_wh.get("creation_draft"))
    assert res_wh.get("entity") == "Warehouses"
    assert res_wh.get("creation_draft", {}).get("WarehouseCode") == "WH-NORTH"
    print("[OK] Test 5 Passed: Warehouse creation parsed successfully!")

    # 6. Test Granular Attribute Retrieval across all 3 master data types
    print("\n--- TEST 6: Granular Attribute Retrieval ---")
    q1 = await agent_service.process_chat("What is the address of customer C20000?")
    print("Q1 (BP Address):", q1.get("granular_answer"))
    assert q1.get("success") == True
    assert "Mumbai" in str(q1.get("reply")) or "BKC" in str(q1.get("reply")) or "Address" in str(q1.get("reply"))

    q2 = await agent_service.process_chat("What is the tax rate of item ITM-001?")
    print("Q2 (Item Tax Rate):", q2.get("granular_answer"))
    assert q2.get("success") == True

    q3 = await agent_service.process_chat("Where is warehouse 01 located?")
    print("Q3 (Warehouse Location):", q3.get("granular_answer"))
    assert q3.get("success") == True

    q4 = await agent_service.process_chat("What is the stock of item ITM-001?")
    print("Q4 (Item Stock):", q4.get("granular_answer"))
    assert q4.get("success") == True

    q5 = await agent_service.process_chat("Show item ITM-001")
    print("Q5 (Show Item):", q5.get("action"), "Records:", len(q5.get("records", [])))
    assert q5.get("success") == True and len(q5.get("records", [])) > 0
    print("[OK] Test 6 Passed: Granular retrieval across all entities succeeded!")

    # 7. Test Universal Field Updates across all 3 master data types
    print("\n--- TEST 7: Universal Field Updates ---")
    u1 = await agent_service.process_chat("Update warehouse 01 city to Thane")
    print("U1 (Warehouse Update):", u1.get("update_result"))
    assert u1.get("success") == True
    assert u1.get("update_result", {}).get("updated_fields", {}).get("City") == "Thane"

    u2 = await agent_service.process_chat("Update item ITM-001 name to Ultra High Strength Bearing 6205")
    print("U2 (Item Update):", u2.get("update_result"))
    assert u2.get("success") == True
    assert u2.get("update_result", {}).get("updated_fields", {}).get("ItemName") == "Ultra High Strength Bearing 6205"

    u3 = await agent_service.process_chat("Update phone to 9876543210 for customer C20000")
    print("U3 (BP Phone Update):", u3.get("update_result"))
    assert u3.get("success") == True
    assert u3.get("update_result", {}).get("updated_fields", {}).get("Phone1") == "9876543210"
    print("[OK] Test 7 Passed: Universal prompt updates verified across Items, BPs, and Warehouses!")

    # 8. Test Live Master Data Querying
    print("\n--- TEST 8: Live Master Data Queries ---")
    list_items = await agent_service.process_chat("List all items")
    print("List Items Count:", len(list_items.get("records", [])))
    assert list_items.get("success") == True and len(list_items.get("records", [])) > 0

    list_bp = await agent_service.process_chat("Give me top 20 Business Partners")
    print("List BP Count:", len(list_bp.get("records", [])))
    assert list_bp.get("success") == True and len(list_bp.get("records", [])) > 0

    list_wh = await agent_service.process_chat("List all Warehouses")
    print("List Warehouses Count:", len(list_wh.get("records", [])))
    assert list_wh.get("success") == True and len(list_wh.get("records", [])) > 0
    print("[OK] Test 8 Passed: Live table queries working perfectly!")

    print("\n========================================================")
    print("ALL 8 HEY CIRA MASTER DATA WORKFLOW TEST SUITES PASSED!")
    print("========================================================")

if __name__ == "__main__":
    asyncio.run(test_all_agent_workflows())
