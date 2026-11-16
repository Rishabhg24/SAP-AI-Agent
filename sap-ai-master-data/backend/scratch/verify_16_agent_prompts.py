import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
from app.services.agent_service import AgentService

prompts = [
    "Show me all active items with Item Code, Item Name, Item Group and Inventory UoM.",
    "Find items where the HSN or Inventory UoM is missing.",
    "Find duplicate or similar item names in the Item Master.",
    "Show me all items created in the last 30 days with their creation date and creator.",
    "Show me items that are inactive but still have stock available.",
    "List items with stock available in each warehouse, including total quantity.",
    "Find the minimum and maximum item details",
    "List item with ordered and committed quantity",
    "Show me all active customers and vendors with their master data details.",
    "Find customers and vendors with missing or incomplete master data such as GSTIN, PAN, payment terms, currency or contact details.",
    "Identify duplicate or similar customer and vendor master records.",
    "Show me customers and vendors created in the last 30 days, including creation date and creator.",
    "Find customers and vendors with missing or incorrect GSTIN/PAN details.",
    "Show me vendors with missing payment terms, bank details or payment methods.",
    "Identify inactive customers or vendors who still have outstanding balances.",
    "Show me customers and vendors with overdue balances and their aging details."
]

async def test_agent_handle_message():
    print(f"Testing AgentService.handle_message with {len(prompts)} prompts...\n")
    for idx, prompt in enumerate(prompts, 1):
        res = await AgentService.handle_message(message=prompt, session_id=f"test-session-{idx}")
        assert res["success"] is True, f"Prompt {idx} failed: {res}"
        assert res["action"] == "QUERY", f"Prompt {idx} action not QUERY: {res.get('action')}"
        assert "reply" in res and len(res["reply"]) > 20, f"Prompt {idx} reply empty!"
        assert "records" in res, f"Prompt {idx} missing records!"
        first_line = res["reply"].split("\n")[0]
        print(f"[{idx:02d}/16] OK | Entity: {res.get('entity')} | Total: {res.get('total')} | Header: {first_line}")

if __name__ == "__main__":
    asyncio.run(test_agent_handle_message())
