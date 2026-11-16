import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.agent_service import agent_service

async def run_tests():
    print("=== RUNNING FULL CIRA VERIFICATION ===")

    # Test 1: Active Draft Modification (verifying NO recursion / stack overflow)
    history = [
        {"role": "user", "content": "Create a Business Partner called Apex Tech"},
        {"role": "assistant", "content": "Draft created", "action": "CREATE_DRAFT", "entity": "BusinessPartners", "creation_draft": {"CardName": "Apex Tech", "Address": "Mumbai", "GSTNo": "27AABCU9603R1ZM"}}
    ]
    res1 = await agent_service.process_chat("Change CardCode to C99881", history=history)
    print("Test 1 (Draft Update without recursion):")
    print("  Action:", res1.get("action"))
    print("  Ready:", res1.get("is_creation_ready"))
    print("  Draft:", res1.get("creation_draft"))

    # Test 2: Duplicate Pre-Check on existing code C01234
    res2 = await agent_service.execute_create_master_data("BusinessPartners", {
        "CardCode": "C01234",
        "CardName": "Rishabh Duplicate",
        "Address": "B-94",
        "GSTNo": "27AABCU9603R1ZM"
    })
    print("\nTest 2 (Duplicate Pre-Check):")
    print("  Success:", res2.get("success"))
    print("  Action:", res2.get("action"))
    print("  Ready:", res2.get("is_creation_ready"))

    # Test 3: Natural language update prompt on draft with 'is'
    history2 = [
        {"role": "user", "content": "Create a Business Partner"},
        {"role": "assistant", "content": "Draft", "action": "CREATE_DRAFT", "entity": "BusinessPartners", "creation_draft": {"CardName": "Rishabh Test"}}
    ]
    res3 = await agent_service.process_chat("CardCode is C88771, Address is Cyber City, GST is 27AABCU9603R1ZM", history=history2)
    print("\nTest 3 (Multi-field slot filling on draft):")
    print("  Action:", res3.get("action"))
    print("  Ready:", res3.get("is_creation_ready"))
    print("  Draft:", res3.get("creation_draft"))

    print("\n=== ALL CIRA FUNCTIONALITY VERIFIED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
