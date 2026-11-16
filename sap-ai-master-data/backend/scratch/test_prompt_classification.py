import re

prompts = [
    ("1. ACTIVE_ITEMS", "Show me all active items with Item Code, Item Name, Item Group and Inventory UoM."),
    ("2. MISSING_HSN_OR_UOM", "Find items where the HSN or Inventory UoM is missing."),
    ("3. DUPLICATE_ITEMS", "Find duplicate or similar item names in the Item Master."),
    ("4. ITEMS_LAST_30_DAYS", "Show me all items created in the last 30 days with their creation date and creator."),
    ("5. INACTIVE_ITEMS_WITH_STOCK", "Show me items that are inactive but still have stock available."),
    ("6. ITEMS_WAREHOUSE_STOCK", "List items with stock available in each warehouse, including total quantity."),
    ("7. MIN_MAX_ITEMS", "Find the minimum and maximum item details"),
    ("8. ORDERED_COMMITTED_ITEMS", "List item with ordered and committed quantity"),
    ("9. ACTIVE_CUSTOMERS_VENDORS", "Show me all active customers and vendors with their master data details."),
    ("10. INCOMPLETE_BP_MASTER", "Find customers and vendors with missing or incomplete master data such as GSTIN, PAN, payment terms, currency or contact details."),
    ("11. DUPLICATE_BP", "Identify duplicate or similar customer and vendor master records."),
    ("12. BP_LAST_30_DAYS", "Show me customers and vendors created in the last 30 days, including creation date and creator."),
    ("13. MISSING_INCORRECT_GSTIN_PAN", "Find customers and vendors with missing or incorrect GSTIN/PAN details."),
    ("14. VENDORS_MISSING_TERMS_BANK", "Show me vendors with missing payment terms, bank details or payment methods."),
    ("15. INACTIVE_BP_WITH_BALANCE", "Identify inactive customers or vendors who still have outstanding balances."),
    ("16. OVERDUE_AGING_BP", "Show me customers and vendors with overdue balances and their aging details.")
]

def classify_prompt(prompt: str) -> str:
    m = prompt.lower().strip()
    
    # 1. Missing HSN or UOM
    if re.search(r"\b(?:hsn|sac)\b", m) and re.search(r"\b(?:inventory\s*uom|uom|unit)\b", m) and re.search(r"\b(?:missing|without|not\s+available|none|empty)\b", m):
        return "MISSING_HSN_OR_UOM"
    if re.search(r"\bmissing\s+(?:hsn|inventory\s*uom|uom)\b", m) and "item" in m:
        return "MISSING_HSN_OR_UOM"

    # 2. Inactive items with stock
    if re.search(r"\binactive\b", m) and re.search(r"\b(?:stock|inventory|quantity)\b", m) and ("item" in m or not any(bp in m for bp in ["customer", "vendor", "supplier", "partner"])):
        return "INACTIVE_ITEMS_WITH_STOCK"

    # 3. Warehouse stock
    if (re.search(r"\bitems?\b", m) and re.search(r"\bstock\b", m) and re.search(r"\b(?:in\s+each\s+warehouse|by\s+warehouse|each\s+warehouse|across\s+warehouses?)\b", m)) or re.search(r"\b(?:stock|quantity)\s+available\s+in\s+each\s+warehouse\b", m):
        return "ITEMS_WAREHOUSE_STOCK"

    # 4. Ordered and committed
    if re.search(r"\bordered\s+(?:and|&)\s+committed\b", m) or re.search(r"\bcommitted\s+(?:and|&)\s+ordered\b", m):
        return "ORDERED_COMMITTED_ITEMS"

    # 5. Min Max items
    if (re.search(r"\b(?:minimum|min)\s+(?:and|&)\s+(?:maximum|max)\b", m) and "item" in m) or re.search(r"\b(?:minimum|min)\s+(?:and|&)\s+(?:maximum|max)\s+item\s+details\b", m):
        return "MIN_MAX_ITEMS"

    # 6. Items created in last 30 days
    if re.search(r"\bitems?\s+created\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) or (re.search(r"\bcreated\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) and "item" in m):
        return "ITEMS_LAST_30_DAYS"

    # 7. Duplicate items
    if (re.search(r"\b(?:duplicate|similar)\b", m) and re.search(r"\bitem\s*(?:names?|masters?|codes?)\b", m)) or re.search(r"\bduplicate\s+(?:or\s+similar\s+)?items?\b", m):
        return "DUPLICATE_ITEMS"

    # 8. Active items
    if re.search(r"\bactive\s+items?\b", m) and not re.search(r"\binactive\b", m):
        return "ACTIVE_ITEMS"

    # 9. Missing or incorrect GSTIN / PAN
    if re.search(r"\b(?:missing|incorrect)\s+(?:gstin|pan|gst|tax\s*id|gstin/pan)\b", m) or re.search(r"\b(?:gstin|pan|tax\s*id)\s+(?:details\s+)?(?:missing|incorrect)\b", m) or re.search(r"\bmissing\s+or\s+incorrect\s+(?:gstin|pan|gst)\b", m) or "gstin/pan" in m:
        return "MISSING_INCORRECT_GSTIN_PAN"

    # 10. Incomplete BP master data
    if re.search(r"\b(?:missing|incomplete)\s+master\s+data\b", m) or re.search(r"\b(?:customers?|vendors?|suppliers?|partners?|business\s*partners?)\s+with\s+(?:missing|incomplete)\s+master\s+data\b", m):
        return "INCOMPLETE_BP_MASTER"

    # 11. Vendors missing terms / bank
    if re.search(r"\b(?:vendors?|suppliers?)\b", m) and re.search(r"\bmissing\b", m) and re.search(r"\b(?:payment\s*terms|bank\s*details|bank|payment\s*methods|terms)\b", m):
        return "VENDORS_MISSING_TERMS_BANK"

    # 12. Inactive BP with balance
    if re.search(r"\binactive\s+(?:customers?|vendors?|suppliers?|partners?|business\s*partners?|bps?)\b", m) and re.search(r"\b(?:outstanding\s+balances?|balances?|outstanding)\b", m):
        return "INACTIVE_BP_WITH_BALANCE"
    if re.search(r"\binactive\b", m) and any(bp in m for bp in ["customer", "vendor", "partner", "bp"]) and re.search(r"\b(?:outstanding\s+balances?|balances?)\b", m):
        return "INACTIVE_BP_WITH_BALANCE"

    # 13. Overdue / aging BP
    if re.search(r"\boverdue\s+balances?\b", m) or re.search(r"\baging\s+details?\b", m) or (re.search(r"\b(?:overdue|aging)\b", m) and re.search(r"\b(?:balances?|debt|receivables?|payables?)\b", m)):
        return "OVERDUE_AGING_BP"

    # 14. BP created in last 30 days
    if re.search(r"\b(?:customers?|vendors?|suppliers?|partners?|business\s*partners?|bps?)\s+created\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) or (re.search(r"\bcreated\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) and any(bp in m for bp in ["customer", "vendor", "partner", "bp", "supplier"])):
        return "BP_LAST_30_DAYS"

    # 15. Duplicate BP
    if re.search(r"\b(?:duplicate|similar)\b", m) and re.search(r"\b(?:customer|vendor|supplier|partner|business\s*partner|bp)\b", m):
        return "DUPLICATE_BP"

    # 16. Active customers and vendors
    if re.search(r"\bactive\s+(?:customers\s+and\s+vendors|vendors\s+and\s+customers|customers|vendors|suppliers|partners|business\s*partners)\b", m) and not re.search(r"\binactive\b", m):
        return "ACTIVE_CUSTOMERS_VENDORS"

    return "UNKNOWN"

for expected, text in prompts:
    actual = classify_prompt(text)
    print(f"[{'PASS' if expected.split('. ')[1] == actual else 'FAIL'}] {expected} -> {actual}")
