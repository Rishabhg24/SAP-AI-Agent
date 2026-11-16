import sys
import os
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.agent_service import agent_service


async def test_customer_hy_resolution():
    print("=== TEST CASE: change phone to 7505576998 for customer hy ===")

    # Turn 1: User prompt as seen in the screenshot
    user_prompt = "change phone to 7505576998 for customer hy"
    res1 = await agent_service.process_chat(user_prompt)

    print("Turn 1 Action:", res1.get("action"))
    print("Turn 1 Entity:", res1.get("entity"))
    print("Turn 1 Pending Fields:", res1.get("pending_fields"))
    print("Turn 1 Missing Fields:", [m.get("field") for m in res1.get("missing_fields", [])])

    # Assertions for Turn 1:
    assert res1.get("action") == "UPDATE"
    assert res1.get("entity") == "BusinessPartners"
    assert res1.get("pending_fields", {}).get("Phone1") == "7505576998"
    assert any(m.get("field") == "CardCode" for m in res1.get("missing_fields", []))
    assert "Cannot insert the value NULL into column" not in str(res1.get("reply", ""))
    assert "ODBC Driver" not in str(res1.get("reply", ""))
    assert "INSERT fails" not in str(res1.get("reply", ""))

    print("[OK] Turn 1 properly captured phone and requested missing Customer Code without SQL crash!")

    # Turn 2: User provides valid CardCode (e.g., C20000)
    history = [
        {"role": "user", "content": user_prompt},
        {
            "role": "assistant",
            "action": "UPDATE",
            "entity": "BusinessPartners",
            "pending_fields": res1.get("pending_fields"),
            "missing_fields": res1.get("missing_fields"),
            "reply": res1.get("reply")
        }
    ]

    res2 = await agent_service.process_chat("C20000", history=history)
    print("Turn 2 Action:", res2.get("action"))
    print("Turn 2 Update Result:", res2.get("update_result"))

    assert res2.get("action") == "UPDATE"
    assert res2.get("update_result") is not None
    assert res2.get("update_result", {}).get("key") == "C20000"
    assert res2.get("update_result", {}).get("updated_fields", {}).get("Phone1") == "7505576998"

    print("[OK] Turn 2 successfully resolved CardCode C20000 and patched Phone1!")

    # Turn 3: User attempts to update a non-existent record code directly
    res3 = await agent_service.process_chat("change phone to 7505576998 for customer C99999")
    print("Turn 3 Success:", res3.get("success"))
    print("Turn 3 Reply Excerpt:", res3.get("reply", "")[:120].replace("\n", " "))

    assert res3.get("success") == False
    assert "Not Found in SAP Business One" in res3.get("reply", "")
    assert "Cannot insert the value NULL into column" not in str(res3.get("reply", ""))

    print("[OK] Turn 3 cleanly informs user about non-existent record with no SQL Server leaks!")
    print("\nALL REPRODUCTION AND RESOLUTION CHECKS PASSED PERFECTLY!")


if __name__ == "__main__":
    asyncio.run(test_customer_hy_resolution())
