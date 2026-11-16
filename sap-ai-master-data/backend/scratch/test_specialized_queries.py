import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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

print(f"Total prompts to support: {len(prompts)}")
