import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.agent_service import AgentService

async def test_user_screenshot_bug():
    print("=== TESTING EXACT REPRODUCTION OF USER SCREENSHOT ===")
    
    # 1. State from Screenshot: User had created Item draft with ItemCode ITM-024 and InventoryUOM PCS
    history = [
        {
            "role": "user",
            "content": "create item master with item code ITM-024 and uom PCS"
        },
        {
            "role": "assistant",
            "action": "CREATE_DRAFT",
            "entity": "Items",
            "creation_draft": {
                "ItemCode": "ITM-024",
                "InventoryUOM": "PCS"
            },
            "missing_fields": [
                {
                    "field": "ItemName",
                    "label": "Item Name / Description (ItemName)",
                    "example": "Stainless Steel Hex Bolt M8",
                    "mandatory": True
                }
            ],
            "is_creation_ready": False
        }
    ]
    
    # User sends "ItemName is Eggs" (just like in the screenshot)
    user_prompt = "ItemName is Eggs"
    res = await AgentService.process_chat(user_prompt, history=history)
    
    print(f"\nPrompt: '{user_prompt}'")
    print(f"Action: {res.get('action')}")
    print(f"Entity: {res.get('entity')}")
    print(f"Draft: {res.get('creation_draft')}")
    print(f"Ready: {res.get('is_creation_ready')}")
    print(f"Missing: {res.get('missing_fields')}")
    
    assert res.get("entity") == "Items", f"Expected entity 'Items', got '{res.get('entity')}'"
    assert res.get("action") == "CREATE_READY", f"Expected action 'CREATE_READY', got '{res.get('action')}'"
    assert res.get("is_creation_ready") == True, "Expected is_creation_ready to be True"
    assert res.get("creation_draft", {}).get("ItemName") == "Eggs", f"Expected ItemName 'Eggs', got {res.get('creation_draft', {}).get('ItemName')}"
    assert res.get("creation_draft", {}).get("ItemCode") == "ITM-024", f"Expected ItemCode 'ITM-024'"
    
    print("\n[OK] TEST PASSED: 'ItemName is Eggs' correctly updated the Item Master draft!")
    
    # Test variation: user just sends "Fresh Country Eggs"
    user_prompt_2 = "Fresh Country Eggs"
    res_2 = await AgentService.process_chat(user_prompt_2, history=history)
    print(f"\nPrompt 2: '{user_prompt_2}'")
    print(f"Action: {res_2.get('action')}")
    print(f"Entity: {res_2.get('entity')}")
    print(f"Draft: {res_2.get('creation_draft')}")
    assert res_2.get("entity") == "Items"
    assert res_2.get("action") == "CREATE_READY"
    assert res_2.get("creation_draft", {}).get("ItemName") == "Fresh Country Eggs"
    print("\n[OK] TEST PASSED: Standalone value 'Fresh Country Eggs' correctly filled ItemName!")

    # Test explicit switch to Business Partner
    user_prompt_3 = "create business partner Acme Corp Mumbai GST 27AABCU9603R1ZM"
    res_3 = await AgentService.process_chat(user_prompt_3, history=history)
    print(f"\nPrompt 3: '{user_prompt_3}'")
    print(f"Entity: {res_3.get('entity')}")
    print(f"Draft: {res_3.get('creation_draft')}")
    assert res_3.get("entity") == "BusinessPartners"
    assert "ItemCode" not in res_3.get("creation_draft", {})
    assert res_3.get("creation_draft", {}).get("CardName") == "Acme Corp"
    print("\n[OK] TEST PASSED: Explicit switch to Business Partner cleanly isolated!")

if __name__ == "__main__":
    asyncio.run(test_user_screenshot_bug())
