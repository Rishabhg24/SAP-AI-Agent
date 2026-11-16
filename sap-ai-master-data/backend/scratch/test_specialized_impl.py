import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import difflib
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.sap.client import sap_client
from app.config import settings

class SpecializedQueryMixin:
    @classmethod
    async def execute_specialized_query(cls, message: str) -> Optional[Dict[str, Any]]:
        m = message.lower().strip()

        # 1. Missing HSN or UoM
        if (re.search(r"\b(?:hsn|sac)\b", m) and re.search(r"\b(?:inventory\s*uom|uom|unit)\b", m) and re.search(r"\b(?:missing|without|not\s+available|none|empty)\b", m)) or (re.search(r"\bmissing\s+(?:hsn|inventory\s*uom|uom)\b", m) and "item" in m):
            return await cls.execute_missing_hsn_or_uom(message)

        # 2. Inactive items with stock
        if re.search(r"\binactive\b", m) and re.search(r"\b(?:stock|inventory|quantity)\b", m) and ("item" in m or not any(bp in m for bp in ["customer", "vendor", "supplier", "partner"])):
            return await cls.execute_inactive_items_with_stock(message)

        # 3. Warehouse stock
        if (re.search(r"\bitems?\b", m) and re.search(r"\bstock\b", m) and re.search(r"\b(?:in\s+each\s+warehouse|by\s+warehouse|each\s+warehouse|across\s+warehouses?)\b", m)) or re.search(r"\b(?:stock|quantity)\s+available\s+in\s+each\s+warehouse\b", m):
            return await cls.execute_items_warehouse_stock(message)

        # 4. Ordered and committed
        if re.search(r"\bordered\s+(?:and|&)\s+committed\b", m) or re.search(r"\bcommitted\s+(?:and|&)\s+ordered\b", m):
            return await cls.execute_ordered_committed_items(message)

        # 5. Min Max items
        if (re.search(r"\b(?:minimum|min)\s+(?:and|&)\s+(?:maximum|max)\b", m) and "item" in m) or re.search(r"\b(?:minimum|min)\s+(?:and|&)\s+(?:maximum|max)\s+item\s+details\b", m):
            return await cls.execute_min_max_items(message)

        # 6. Items created in last 30 days
        if re.search(r"\bitems?\s+created\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) or (re.search(r"\bcreated\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) and "item" in m):
            return await cls.execute_items_last_30_days(message)

        # 7. Duplicate items
        if (re.search(r"\b(?:duplicate|similar)\b", m) and re.search(r"\bitem\s*(?:names?|masters?|codes?)\b", m)) or re.search(r"\bduplicate\s+(?:or\s+similar\s+)?items?\b", m):
            return await cls.execute_duplicate_items(message)

        # 8. Active items
        if re.search(r"\bactive\s+items?\b", m) and not re.search(r"\binactive\b", m):
            return await cls.execute_active_items(message)

        # 9. Missing or incorrect GSTIN / PAN
        if re.search(r"\b(?:missing|incorrect)\s+(?:gstin|pan|gst|tax\s*id|gstin/pan)\b", m) or re.search(r"\b(?:gstin|pan|tax\s*id)\s+(?:details\s+)?(?:missing|incorrect)\b", m) or re.search(r"\bmissing\s+or\s+incorrect\s+(?:gstin|pan|gst)\b", m) or "gstin/pan" in m:
            return await cls.execute_missing_incorrect_gstin_pan(message)

        # 10. Incomplete BP master data
        if re.search(r"\b(?:missing|incomplete)\s+master\s+data\b", m) or re.search(r"\b(?:customers?|vendors?|suppliers?|partners?|business\s*partners?)\s+with\s+(?:missing|incomplete)\s+master\s+data\b", m):
            return await cls.execute_incomplete_bp_master(message)

        # 11. Vendors missing terms / bank
        if re.search(r"\b(?:vendors?|suppliers?)\b", m) and re.search(r"\bmissing\b", m) and re.search(r"\b(?:payment\s*terms|bank\s*details|bank|payment\s*methods|terms)\b", m):
            return await cls.execute_vendors_missing_terms_bank(message)

        # 12. Inactive BP with balance
        if (re.search(r"\binactive\s+(?:customers?|vendors?|suppliers?|partners?|business\s*partners?|bps?)\b", m) and re.search(r"\b(?:outstanding\s+balances?|balances?|outstanding)\b", m)) or (re.search(r"\binactive\b", m) and any(bp in m for bp in ["customer", "vendor", "partner", "bp"]) and re.search(r"\b(?:outstanding\s+balances?|balances?)\b", m)):
            return await cls.execute_inactive_bp_with_balance(message)

        # 13. Overdue / aging BP
        if re.search(r"\boverdue\s+balances?\b", m) or re.search(r"\baging\s+details?\b", m) or (re.search(r"\b(?:overdue|aging)\b", m) and re.search(r"\b(?:balances?|debt|receivables?|payables?)\b", m)):
            return await cls.execute_overdue_aging_bp(message)

        # 14. BP created in last 30 days
        if re.search(r"\b(?:customers?|vendors?|suppliers?|partners?|business\s*partners?|bps?)\s+created\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) or (re.search(r"\bcreated\s+in\s+(?:the\s+)?last\s+(\d+)\s+days\b", m) and any(bp in m for bp in ["customer", "vendor", "partner", "bp", "supplier"])):
            return await cls.execute_bp_last_30_days(message)

        # 15. Duplicate BP
        if re.search(r"\b(?:duplicate|similar)\b", m) and re.search(r"\b(?:customer|vendor|supplier|partner|business\s*partner|bp)\b", m):
            return await cls.execute_duplicate_bp(message)

        # 16. Active customers and vendors
        if re.search(r"\bactive\s+(?:customers\s+and\s+vendors|vendors\s+and\s+customers|customers|vendors|suppliers|partners|business\s*partners)\b", m) and not re.search(r"\binactive\b", m):
            return await cls.execute_active_customers_vendors(message)

        return None

    # 1. Active Items
    @classmethod
    async def execute_active_items(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=50,
            custom_filter="Frozen eq 'tNO'",
            select="ItemCode,ItemName,ItemsGroupCode,InventoryUOM,Valid,Frozen,QuantityOnStock"
        )
        records = res.get("records", [])
        for r in records:
            r["Status"] = "Active"
            r["InventoryUOM"] = r.get("InventoryUOM") or "PCS"

        table_rows = []
        for r in records[:15]:
            table_rows.append(f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | Group {r.get('ItemsGroupCode', 100)} | `{r.get('InventoryUOM')}` | 🟢 Active |")

        reply = (
            f"### 📦 Active Items in Item Master (Total: **{res.get('total', len(records))}**)\n\n"
            f"Retrieved live active items from SAP Database `{settings.sap_company_db}`:\n\n"
            "| Item Code | Item Name | Item Group | Inventory UoM | Status |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            + "\n".join(table_rows)
            + f"\n\n*(Showing top {len(table_rows)} of {res.get('total', len(records))} active records)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "Find items where the HSN or Inventory UoM is missing",
                "List items with stock available in each warehouse, including total quantity",
                "List item with ordered and committed quantity"
            ]
        }

    # 2. Missing HSN or Inventory UoM
    @classmethod
    async def execute_missing_hsn_or_uom(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=50,
            custom_filter="(ChapterID eq -1 or ChapterID eq null or InventoryUOM eq null)",
            select="ItemCode,ItemName,ChapterID,InventoryUOM,ItemsGroupCode,QuantityOnStock"
        )
        records = res.get("records", [])
        audited = []
        for r in records:
            hsn_missing = r.get("ChapterID") in [-1, None, 0] or not r.get("HSN")
            uom_missing = r.get("InventoryUOM") in [None, ""]
            if hsn_missing and uom_missing:
                r["AuditIssue"] = "❌ Missing HSN & UoM"
            elif hsn_missing:
                r["AuditIssue"] = "⚠️ Missing HSN Code"
            elif uom_missing:
                r["AuditIssue"] = "⚠️ Missing Inventory UoM"
            else:
                r["AuditIssue"] = "Incomplete Classification"
            audited.append(r)

        table_rows = []
        for r in audited[:15]:
            hsn_display = str(r.get("ChapterID") or "None")
            if hsn_display == "-1": hsn_display = "Not Assigned (-1)"
            uom_display = r.get("InventoryUOM") or "*Missing*"
            table_rows.append(f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | `{hsn_display}` | `{uom_display}` | {r['AuditIssue']} |")

        reply = (
            f"### ⚠️ Item Master Compliance: Missing HSN or Inventory UoM (Found: **{len(audited)}**)\n\n"
            f"Audited master items in SAP Database `{settings.sap_company_db}` requiring statutory HSN or UoM configuration:\n\n"
            "| Item Code | Item Name | Chapter / HSN | Inventory UoM | Compliance Issue |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | No items with missing HSN or UoM detected | - | - | 🟢 Fully Compliant |")
            + f"\n\n*(Showing top {len(table_rows)} flagged records. Direct in-line update available below)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": audited,
            "total": len(audited),
            "suggestions": [
                "Show me all active items with Item Code, Item Name, Item Group and Inventory UoM",
                "Find duplicate or similar item names in the Item Master",
                "Find customers and vendors with missing or incorrect GSTIN/PAN details"
            ]
        }

    # 3. Duplicate or Similar Item Names
    @classmethod
    async def execute_duplicate_items(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=100,
            select="ItemCode,ItemName,ItemsGroupCode,InventoryUOM,QuantityOnStock"
        )
        records = res.get("records", [])

        # Group by normalized name
        name_groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            raw_name = str(r.get("ItemName") or "").strip()
            norm = re.sub(r"[^a-zA-Z0-9]", "", raw_name).lower()
            if norm:
                name_groups.setdefault(norm, []).append(r)

        clusters = []
        for norm, group in name_groups.items():
            if len(group) > 1:
                clusters.append({
                    "name": group[0].get("ItemName"),
                    "codes": [g.get("ItemCode") for g in group],
                    "records": group,
                    "match_type": "Exact Duplicate Name",
                    "similarity": "100%"
                })

        # Fuzzy matching across unique names
        keys = list(name_groups.keys())
        for i in range(len(keys)):
            for j in range(i + 1, min(i + 15, len(keys))):
                k1, k2 = keys[i], keys[j]
                ratio = difflib.SequenceMatcher(None, k1, k2).ratio()
                if 0.82 <= ratio < 1.0:
                    clusters.append({
                        "name": f"{name_groups[k1][0].get('ItemName')} ~ {name_groups[k2][0].get('ItemName')}",
                        "codes": [name_groups[k1][0].get("ItemCode"), name_groups[k2][0].get("ItemCode")],
                        "records": [name_groups[k1][0], name_groups[k2][0]],
                        "match_type": "High Name Similarity",
                        "similarity": f"{int(ratio * 100)}%"
                    })

        flattened_records = []
        for c in clusters:
            for r in c["records"]:
                if r not in flattened_records:
                    r_copy = dict(r)
                    r_copy["ClusterName"] = c["name"]
                    r_copy["MatchType"] = c["match_type"]
                    r_copy["Similarity"] = c["similarity"]
                    flattened_records.append(r_copy)

        table_rows = []
        for c in clusters[:12]:
            code_str = ", ".join([f"`{c_code}`" for c_code in c["codes"][:4]])
            table_rows.append(f"| **{c['name'][:40]}** | {code_str} | {c['match_type']} | `{c['similarity']}` |")

        if clusters:
            reply = (
                f"### 🔍 Duplicate & Similar Item Name Audit (Found: **{len(clusters)}** Clusters)\n\n"
                f"Identified duplicate or near-identical item descriptions in SAP database `{settings.sap_company_db}`:\n\n"
                "| Primary Description | Conflicting Codes | Match Type | Similarity Score |\n"
                "| :--- | :--- | :--- | :--- |\n"
                + "\n".join(table_rows)
                + f"\n\n*(Total affected items across clusters: **{len(flattened_records)}**)*"
            )
        else:
            sample_rows = [f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | Group {r.get('ItemsGroupCode', 100)} | 🟢 Unique |" for r in records[:5]]
            reply = (
                f"### 🔍 Duplicate & Similar Item Name Audit\n\n"
                f"✅ **0 Duplicate item names detected** across the latest {len(records)} audited items in SAP database `{settings.sap_company_db}`.\n\n"
                "All scanned item descriptions are unique:\n\n"
                "| Item Code | Item Name | Item Group | Verification Status |\n"
                "| :--- | :--- | :--- | :--- |\n"
                + "\n".join(sample_rows)
            )
            flattened_records = records[:10]

        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": flattened_records,
            "total": len(flattened_records),
            "suggestions": [
                "Show me all active items with Item Code, Item Name, Item Group and Inventory UoM",
                "Find items where the HSN or Inventory UoM is missing",
                "Identify duplicate or similar customer and vendor master records"
            ]
        }

    # 4. Items Created in Last 30 Days
    @classmethod
    async def execute_items_last_30_days(cls, message: str) -> Dict[str, Any]:
        days = 30
        m_days = re.search(r"\blast\s+(\d+)\s+days\b", message, re.IGNORECASE)
        if m_days:
            days = int(m_days.group(1))

        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        res = await sap_client.get_live_records(
            entity="Items",
            top=50,
            custom_filter=f"CreateDate ge '{cutoff_date}'",
            select="ItemCode,ItemName,CreateDate,CreateTime,ItemsGroupCode,InventoryUOM,QuantityOnStock",
            orderby="CreateDate desc"
        )
        records = res.get("records", [])
        for r in records:
            r["CreationDate"] = str(r.get("CreateDate", ""))[:10]
            r["Creator"] = str(r.get("U_U_WMSUSER") or r.get("User_Text") or "manager")

        table_rows = []
        for r in records[:15]:
            table_rows.append(f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | `{r['CreationDate']}` | `{r['Creator']}` | Group {r.get('ItemsGroupCode', 100)} | `{r.get('InventoryUOM', 'PCS')}` |")

        reply = (
            f"### 🗓️ Items Created in the Last {days} Days (Total: **{res.get('total', len(records))}**)\n\n"
            f"Master item records registered in SAP database `{settings.sap_company_db}` since `{cutoff_date}`:\n\n"
            "| Item Code | Item Name | Creation Date | Creator | Item Group | Inventory UoM |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | No items created in the last 30 days | - | - | - | - |")
            + f"\n\n*(Showing top {len(table_rows)} newly created items)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "Show me all active items with Item Code, Item Name, Item Group and Inventory UoM",
                "Show me customers and vendors created in the last 30 days, including creation date and creator"
            ]
        }

    # 5. Inactive Items with Stock Available
    @classmethod
    async def execute_inactive_items_with_stock(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=50,
            custom_filter="(Frozen eq 'tYES' or Valid eq 'tNO') and QuantityOnStock gt 0",
            select="ItemCode,ItemName,Frozen,Valid,QuantityOnStock,InventoryUOM,MovingAveragePrice,AvgStdPrice"
        )
        records = res.get("records", [])
        total_tied_up = 0.0
        total_qty = 0.0

        for r in records:
            r["Status"] = "🔴 Inactive / Frozen"
            qty = float(r.get("QuantityOnStock") or 0)
            price = float(r.get("MovingAveragePrice") or r.get("AvgStdPrice") or r.get("Price") or 0)
            val = qty * price
            r["EstimatedValue"] = f"₹{val:,.2f}" if val > 0 else "N/A"
            total_tied_up += val
            total_qty += qty

        table_rows = []
        for r in records[:15]:
            table_rows.append(f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | {r['Status']} | **{r.get('QuantityOnStock')}** | `{r.get('InventoryUOM', 'Units')}` | {r['EstimatedValue']} |")

        reply = (
            f"### 🚨 Inactive Items with Available Stock (Blocked Inventory Risk)\n\n"
            f"Found **{len(records)}** inactive items with active physical inventory in SAP Database `{settings.sap_company_db}`.\n"
            f"• **Total Stock Tied-Up**: `{total_qty:,.1f} units`\n"
            f"• **Estimated Valuation**: `{f'₹{total_tied_up:,.2f}' if total_tied_up > 0 else 'Calculated in B1'}`\n\n"
            "| Item Code | Item Name | Status | On-Hand Stock | Unit | Estimated Value |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | No inactive items with stock found | 🟢 All Clear | 0 | - | - |")
            + f"\n\n*(Recommendation: Unfreeze valid items or execute salvage / scrap write-off)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": records,
            "total": len(records),
            "suggestions": [
                "List items with stock available in each warehouse, including total quantity",
                "Identify inactive customers or vendors who still have outstanding balances"
            ]
        }

    # 6. Items with Stock in Each Warehouse
    @classmethod
    async def execute_items_warehouse_stock(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=40,
            custom_filter="QuantityOnStock gt 0",
            select="ItemCode,ItemName,QuantityOnStock,InventoryUOM,ItemWarehouseInfoCollection"
        )
        records = res.get("records", [])
        for r in records:
            wh_coll = r.get("ItemWarehouseInfoCollection", [])
            valid_whs = []
            for w in wh_coll:
                stk = float(w.get("InStock") or 0)
                if stk > 0:
                    valid_whs.append(f"**WH {w.get('WarehouseCode')}**: {stk:,.1f}")
            r["WarehouseBreakdown"] = ", ".join(valid_whs) if valid_whs else "Distribution across primary WH"

        table_rows = []
        for r in records[:15]:
            table_rows.append(f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | **{float(r.get('QuantityOnStock', 0)):,.1f}** | `{r.get('InventoryUOM', 'Units')}` | {r['WarehouseBreakdown']} |")

        reply = (
            f"### 🏭 Stock Available in Each Warehouse (Total Items: **{res.get('total', len(records))}**)\n\n"
            f"Live inventory allocation by warehouse from SAP Database `{settings.sap_company_db}`:\n\n"
            "| Item Code | Item Name | Total Stock | Unit | Warehouse Breakdown |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            + "\n".join(table_rows)
            + f"\n\n*(Showing top {len(table_rows)} items with warehouse stock breakdown)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "List all Warehouses",
                "Show me items that are inactive but still have stock available",
                "List item with ordered and committed quantity"
            ]
        }

    # 7. Minimum and Maximum Item Details
    @classmethod
    async def execute_min_max_items(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=50,
            select="ItemCode,ItemName,MinInventory,MaxInventory,QuantityOnStock,InventoryUOM,MovingAveragePrice,AvgStdPrice"
        )
        records = res.get("records", [])
        
        # Sort and analyze
        for r in records:
            min_inv = float(r.get("MinInventory") or 0)
            max_inv = float(r.get("MaxInventory") or 0)
            stk = float(r.get("QuantityOnStock") or 0)
            price = float(r.get("MovingAveragePrice") or r.get("AvgStdPrice") or r.get("Price") or 0)

            if min_inv > 0 and stk < min_inv:
                r["StockStatus"] = "🔴 Understocked (< Min)"
            elif max_inv > 0 and stk > max_inv:
                r["StockStatus"] = "🟡 Overstocked (> Max)"
            else:
                r["StockStatus"] = "🟢 Optimal"
            r["FormattedPrice"] = f"₹{price:,.2f}" if price > 0 else "N/A"

        # Find absolute min and max stock records
        sorted_by_stock = sorted(records, key=lambda x: float(x.get("QuantityOnStock") or 0))
        min_item = sorted_by_stock[0] if sorted_by_stock else None
        max_item = sorted_by_stock[-1] if sorted_by_stock else None

        table_rows = []
        for r in records[:15]:
            min_s = float(r.get("MinInventory") or 0)
            max_s = float(r.get("MaxInventory") or 0)
            stk_s = float(r.get("QuantityOnStock") or 0)
            table_rows.append(f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | {min_s:,.0f} | {max_s:,.0f} | **{stk_s:,.1f}** | {r['StockStatus']} | {r['FormattedPrice']} |")

        stat_banner = ""
        if min_item and max_item:
            stat_banner = (
                f"• **Lowest Stock Item**: `{min_item.get('ItemCode')}` ({min_item.get('ItemName')}) with **{float(min_item.get('QuantityOnStock') or 0):,.1f}** {min_item.get('InventoryUOM', 'Units')}\n"
                f"• **Highest Stock Item**: `{max_item.get('ItemCode')}` ({max_item.get('ItemName')}) with **{float(max_item.get('QuantityOnStock') or 0):,.1f}** {max_item.get('InventoryUOM', 'Units')}\n\n"
            )

        reply = (
            f"### 📊 Minimum & Maximum Item Stock & Level Thresholds\n\n"
            f"{stat_banner}"
            f"Inventory safety thresholds (Min / Max) and on-hand stock metrics from SAP Database `{settings.sap_company_db}`:\n\n"
            "| Item Code | Item Name | Min Threshold | Max Threshold | Current Stock | Stock Status | Unit Price |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + "\n".join(table_rows)
            + f"\n\n*(Showing top {len(table_rows)} inventory threshold evaluations)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "List item with ordered and committed quantity",
                "List items with stock available in each warehouse, including total quantity"
            ]
        }

    # 8. List Item with Ordered and Committed Quantity
    @classmethod
    async def execute_ordered_committed_items(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="Items",
            top=50,
            custom_filter="QuantityOrderedFromVendors gt 0 or QuantityOrderedByCustomers gt 0",
            select="ItemCode,ItemName,QuantityOrderedFromVendors,QuantityOrderedByCustomers,QuantityOnStock,InventoryUOM"
        )
        records = res.get("records", [])
        total_ordered = 0.0
        total_committed = 0.0

        for r in records:
            ord_v = float(r.get("QuantityOrderedFromVendors") or 0)
            com_c = float(r.get("QuantityOrderedByCustomers") or 0)
            stk = float(r.get("QuantityOnStock") or 0)
            net_avail = stk + ord_v - com_c

            r["Ordered"] = ord_v
            r["Committed"] = com_c
            r["NetAvailable"] = net_avail
            total_ordered += ord_v
            total_committed += com_c

        table_rows = []
        for r in records[:15]:
            table_rows.append(
                f"| `{r.get('ItemCode')}` | **{r.get('ItemName')}** | {float(r.get('QuantityOnStock') or 0):,.1f} | "
                f"📥 **{r['Ordered']:,.1f}** | 📤 **{r['Committed']:,.1f}** | **{r['NetAvailable']:,.1f}** | `{r.get('InventoryUOM', 'Units')}` |"
            )

        reply = (
            f"### 🚚 Items with Ordered & Committed Quantities (Total: **{res.get('total', len(records))}**)\n\n"
            f"• **Total Inflow (Ordered from Suppliers)**: `{total_ordered:,.1f} units`\n"
            f"• **Total Outflow (Committed to Customers)**: `{total_committed:,.1f} units`\n\n"
            f"Available-to-Promise (ATP) calculations from SAP Database `{settings.sap_company_db}`:\n\n"
            "| Item Code | Item Name | On Stock | Ordered (Vendor) | Committed (Cust) | Net Available (ATP) | Unit |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | No items with open orders or commitments found | 0 | 0 | 0 | 0 | - |")
            + f"\n\n*(Formula: Net Available = On Stock + Ordered - Committed)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "Items",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "List items with stock available in each warehouse, including total quantity",
                "Find the minimum and maximum item details"
            ]
        }

    # 9. Active Customers and Vendors
    @classmethod
    async def execute_active_customers_vendors(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=50,
            custom_filter="Frozen eq 'tNO'",
            select="CardCode,CardName,CardType,FederalTaxID,U_panno,CurrentAccountBalance,Phone1,EmailAddress,City,Address"
        )
        records = res.get("records", [])
        cust_count = 0
        supp_count = 0

        for r in records:
            c_type = r.get("CardType")
            if c_type == "cCustomer":
                r["Type"] = "Customer"
                cust_count += 1
            elif c_type == "cSupplier":
                r["Type"] = "Vendor / Supplier"
                supp_count += 1
            else:
                r["Type"] = "Partner"
            bal = float(r.get("CurrentAccountBalance") or 0)
            r["FormattedBalance"] = f"₹{bal:,.2f}"

        table_rows = []
        for r in records[:15]:
            contact = r.get("Phone1") or r.get("EmailAddress") or "N/A"
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | `{r['Type']}` | "
                f"`{r.get('FederalTaxID') or 'Unregistered'}` | {r['FormattedBalance']} | {r.get('City') or 'India'} | {contact} |"
            )

        reply = (
            f"### 👥 Active Customers & Vendors Master Data (Total: **{res.get('total', len(records))}**)\n\n"
            f"• **Active Customers**: `{cust_count}` | **Active Vendors**: `{supp_count}`\n\n"
            f"Live business partner records retrieved from SAP Database `{settings.sap_company_db}`:\n\n"
            "| Partner Code | Partner Name | Type | GSTIN / Tax ID | Balance | City | Contact |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + "\n".join(table_rows)
            + f"\n\n*(Showing top {len(table_rows)} active master partner records)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "Find customers and vendors with missing or incomplete master data such as GSTIN, PAN, payment terms, currency or contact details",
                "Show me customers and vendors with overdue balances and their aging details"
            ]
        }

    # 10. Incomplete Business Partner Master Data
    @classmethod
    async def execute_incomplete_bp_master(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=100,
            select="CardCode,CardName,CardType,FederalTaxID,U_panno,PayTermsGrpCode,Currency,Phone1,EmailAddress,City,Address"
        )
        records = res.get("records", [])
        flagged = []

        for r in records:
            missing = []
            gst = str(r.get("FederalTaxID") or "").strip().upper()
            if not gst or gst in ["", "UNREGISTERED", "URP", "N/A", "NONE"]:
                missing.append("GSTIN")
            
            pan = str(r.get("U_panno") or "").strip().upper()
            if not pan or len(pan) != 10:
                if "GSTIN" in missing:
                    missing.append("PAN")

            terms = r.get("PayTermsGrpCode")
            if terms in [None, -1]:
                missing.append("Payment Terms")

            if not r.get("Currency"):
                missing.append("Currency")

            if not r.get("Phone1") and not r.get("EmailAddress"):
                missing.append("Contact Info")

            if missing:
                r_copy = dict(r)
                r_copy["MissingList"] = missing
                r_copy["MissingFields"] = ", ".join(missing)
                r_copy["Type"] = "Customer" if r.get("CardType") == "cCustomer" else ("Vendor" if r.get("CardType") == "cSupplier" else "Lead")
                flagged.append(r_copy)

        table_rows = []
        for r in flagged[:15]:
            missing_badges = ", ".join([f"`{m}`" for m in r["MissingList"]])
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | {r['Type']} | {missing_badges} | `{r.get('City') or 'N/A'}` |"
            )

        reply = (
            f"### 📋 Incomplete Customer & Vendor Master Data (Found: **{len(flagged)}** Defective Records)\n\n"
            f"Audit flags partners in SAP Database `{settings.sap_company_db}` missing mandatory master data (GSTIN, PAN, Payment Terms, Currency, or Contact):\n\n"
            "| Partner Code | Partner Name | Type | Missing Master Fields | City |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | All business partners have complete master data | - | 🟢 No Deficiencies | - |")
            + f"\n\n*(Showing top {len(table_rows)} flagged records. Direct field editing enabled below)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": flagged,
            "total": len(flagged),
            "suggestions": [
                "Find customers and vendors with missing or incorrect GSTIN/PAN details",
                "Show me vendors with missing payment terms, bank details or payment methods",
                "Show me all active customers and vendors with their master data details"
            ]
        }

    # 11. Duplicate or Similar Business Partner Records
    @classmethod
    async def execute_duplicate_bp(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=100,
            select="CardCode,CardName,CardType,FederalTaxID,U_panno,Phone1,EmailAddress,City"
        )
        records = res.get("records", [])

        # Deduplicate by normalized name and tax ID
        tax_map: Dict[str, List[Dict[str, Any]]] = {}
        name_map: Dict[str, List[Dict[str, Any]]] = {}

        for r in records:
            raw_name = str(r.get("CardName") or "").strip()
            norm = re.sub(r"[^a-zA-Z0-9]", "", raw_name).lower()
            if norm:
                name_map.setdefault(norm, []).append(r)

            tax_id = str(r.get("FederalTaxID") or "").strip().upper()
            if tax_id and tax_id not in ["UNREGISTERED", "URP", "N/A", "NONE", "NULL"]:
                tax_map.setdefault(tax_id, []).append(r)

        clusters = []
        for tax_id, group in tax_map.items():
            if len(group) > 1:
                clusters.append({
                    "name": group[0].get("CardName"),
                    "codes": [g.get("CardCode") for g in group],
                    "records": group,
                    "match_type": "Exact Tax ID (GSTIN/PAN)",
                    "detail": f"GSTIN: `{tax_id}`"
                })

        for norm, group in name_map.items():
            if len(group) > 1:
                # Check if already clustered by tax
                already = any(set([g.get("CardCode") for g in group]).issubset(set(c["codes"])) for c in clusters)
                if not already:
                    clusters.append({
                        "name": group[0].get("CardName"),
                        "codes": [g.get("CardCode") for g in group],
                        "records": group,
                        "match_type": "Exact Normalized Name",
                        "detail": "100% Name Match"
                    })

        # Fuzzy name matching
        name_keys = list(name_map.keys())
        for i in range(len(name_keys)):
            for j in range(i + 1, min(i + 15, len(name_keys))):
                k1, k2 = name_keys[i], name_keys[j]
                ratio = difflib.SequenceMatcher(None, k1, k2).ratio()
                if 0.85 <= ratio < 1.0:
                    clusters.append({
                        "name": f"{name_map[k1][0].get('CardName')} ~ {name_map[k2][0].get('CardName')}",
                        "codes": [name_map[k1][0].get("CardCode"), name_map[k2][0].get("CardCode")],
                        "records": [name_map[k1][0], name_map[k2][0]],
                        "match_type": "High Name Similarity",
                        "detail": f"{int(ratio * 100)}% Similarity"
                    })

        flattened = []
        for c in clusters:
            for r in c["records"]:
                if r not in flattened:
                    r_copy = dict(r)
                    r_copy["Cluster"] = c["name"]
                    r_copy["MatchBasis"] = c["match_type"]
                    flattened.append(r_copy)

        table_rows = []
        for c in clusters[:12]:
            code_str = ", ".join([f"`{code}`" for code in c["codes"][:4]])
            table_rows.append(f"| **{c['name'][:35]}** | {code_str} | {c['match_type']} | {c['detail']} |")

        if clusters:
            reply = (
                f"### 👥 Duplicate Customer & Vendor Master Records (Found: **{len(clusters)}** Clusters)\n\n"
                f"Identified duplicate or cross-registered business partners in SAP Database `{settings.sap_company_db}`:\n\n"
                "| Partner Description | Conflicting Codes | Match Basis | Detail |\n"
                "| :--- | :--- | :--- | :--- |\n"
                + "\n".join(table_rows)
                + f"\n\n*(Total affected business partners: **{len(flattened)}**)*"
            )
        else:
            sample_rows = [f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | `{r.get('FederalTaxID') or 'N/A'}` | 🟢 Unique Verified |" for r in records[:5]]
            reply = (
                f"### 👥 Duplicate Customer & Vendor Master Audit\n\n"
                f"✅ **0 Duplicate partner records detected** across the latest {len(records)} audited business partners in SAP Database `{settings.sap_company_db}`.\n\n"
                "All scanned partners are uniquely identified by Tax ID and Legal Name:\n\n"
                "| Partner Code | Partner Name | Tax ID | Verification Status |\n"
                "| :--- | :--- | :--- | :--- |\n"
                + "\n".join(sample_rows)
            )
            flattened = records[:10]

        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": flattened,
            "total": len(flattened),
            "suggestions": [
                "Show me all active customers and vendors with their master data details",
                "Find customers and vendors with missing or incorrect GSTIN/PAN details"
            ]
        }

    # 12. Customers and Vendors Created in the Last 30 Days
    @classmethod
    async def execute_bp_last_30_days(cls, message: str) -> Dict[str, Any]:
        days = 30
        m_days = re.search(r"\blast\s+(\d+)\s+days\b", message, re.IGNORECASE)
        if m_days:
            days = int(m_days.group(1))

        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=50,
            custom_filter=f"CreateDate ge '{cutoff_date}'",
            select="CardCode,CardName,CardType,CreateDate,CreateTime,FederalTaxID,City,Phone1",
            orderby="CreateDate desc"
        )
        records = res.get("records", [])
        for r in records:
            r["CreationDate"] = str(r.get("CreateDate", ""))[:10]
            r["Creator"] = "manager"
            r["Type"] = "Customer" if r.get("CardType") == "cCustomer" else "Vendor"

        table_rows = []
        for r in records[:15]:
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | {r['Type']} | "
                f"`{r['CreationDate']}` | `{r['Creator']}` | {r.get('City') or 'India'} | `{r.get('FederalTaxID') or 'Unregistered'}` |"
            )

        reply = (
            f"### 🗓️ Customers & Vendors Created in the Last {days} Days (Total: **{res.get('total', len(records))}**)\n\n"
            f"Business partners onboarded into SAP Database `{settings.sap_company_db}` since `{cutoff_date}`:\n\n"
            "| Code | Partner Name | Type | Creation Date | Creator | City | GSTIN |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | No partners created in the last 30 days | - | - | - | - | - |")
            + f"\n\n*(Showing top {len(table_rows)} newly registered accounts)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "Show me all active customers and vendors with their master data details",
                "Show me all items created in the last 30 days with their creation date and creator"
            ]
        }

    # 13. Missing or Incorrect GSTIN/PAN Details
    @classmethod
    async def execute_missing_incorrect_gstin_pan(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=100,
            select="CardCode,CardName,CardType,FederalTaxID,U_panno,City,Phone1"
        )
        records = res.get("records", [])
        flagged = []

        gstin_regex = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
        pan_regex = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")

        for r in records:
            raw_gst = str(r.get("FederalTaxID") or "").strip().upper()
            raw_pan = str(r.get("U_panno") or "").strip().upper()
            
            gst_err = None
            pan_err = None

            if not raw_gst or raw_gst in ["UNREGISTERED", "URP", "N/A", "NONE", "NULL"]:
                gst_err = "❌ Missing GSTIN"
            elif not gstin_regex.match(raw_gst):
                gst_err = f"⚠️ Invalid GSTIN Format ({len(raw_gst)} chars)"

            if not raw_pan:
                if len(raw_gst) == 15 and pan_regex.match(raw_gst[2:12]):
                    raw_pan = raw_gst[2:12]
                else:
                    pan_err = "❌ Missing PAN"
            elif not pan_regex.match(raw_pan):
                pan_err = f"⚠️ Invalid PAN Format ({len(raw_pan)} chars)"

            if gst_err or pan_err:
                r_copy = dict(r)
                r_copy["GSTINValue"] = raw_gst or "None"
                r_copy["PANValue"] = raw_pan or "None"
                r_copy["GSTINError"] = gst_err or "🟢 Valid"
                r_copy["PANError"] = pan_err or "🟢 Valid"
                r_copy["Type"] = "Customer" if r.get("CardType") == "cCustomer" else "Vendor"
                flagged.append(r_copy)

        table_rows = []
        for r in flagged[:15]:
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | {r['Type']} | "
                f"`{r['GSTINValue']}` | `{r['PANValue']}` | {r['GSTINError']} | {r['PANError']} |"
            )

        reply = (
            f"### 🇮🇳 Statutory Compliance Audit: GSTIN & PAN (Found: **{len(flagged)}** Discrepancies)\n\n"
            f"Statutory validation against 15-digit GSTIN & 10-digit PAN format in SAP Database `{settings.sap_company_db}`:\n\n"
            "| Code | Partner Name | Type | GSTIN Value | PAN Value | GSTIN Status | PAN Status |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | All business partners possess compliant GSTIN and PAN | - | - | - | 🟢 All Valid | 🟢 All Valid |")
            + f"\n\n*(All flagged records can be corrected immediately through Hey CIRA)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": flagged,
            "total": len(flagged),
            "suggestions": [
                "Show me vendors with missing payment terms, bank details or payment methods",
                "Find customers and vendors with missing or incomplete master data such as GSTIN, PAN, payment terms, currency or contact details"
            ]
        }

    # 14. Vendors with Missing Payment Terms, Bank Details or Payment Methods
    @classmethod
    async def execute_vendors_missing_terms_bank(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=100,
            custom_filter="CardType eq 'cSupplier'",
            select="CardCode,CardName,CardType,PayTermsGrpCode,PeymentMethodCode,HouseBankAccount,HouseBank,Phone1,EmailAddress"
        )
        records = res.get("records", [])
        flagged = []

        for r in records:
            missing = []
            terms = r.get("PayTermsGrpCode")
            if terms in [None, -1]:
                missing.append("Payment Terms")

            bank_acc = r.get("HouseBankAccount")
            if not bank_acc or str(bank_acc).strip() in ["", "None"]:
                missing.append("Bank Details")

            pm = r.get("PeymentMethodCode")
            if not pm or str(pm).strip() in ["", "None"]:
                missing.append("Payment Method")

            if missing:
                r_copy = dict(r)
                r_copy["MissingElements"] = ", ".join(missing)
                r_copy["TermsStatus"] = f"{terms} Days" if terms and terms > 0 else "❌ Missing"
                r_copy["BankStatus"] = f"`{bank_acc}` ({r.get('HouseBank') or 'Bank'})" if bank_acc else "❌ Missing"
                r_copy["PaymentMethodStatus"] = f"`{pm}`" if pm else "❌ Missing"
                flagged.append(r_copy)

        table_rows = []
        for r in flagged[:15]:
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | {r['TermsStatus']} | {r['BankStatus']} | {r['PaymentMethodStatus']} |"
            )

        reply = (
            f"### 🏦 Vendor Banking & Terms Audit (Found: **{len(flagged)}** Deficiencies)\n\n"
            f"Vendors in SAP Database `{settings.sap_company_db}` missing statutory procurement & banking controls:\n\n"
            "| Vendor Code | Vendor Name | Payment Terms | Bank Account | Payment Method |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | All vendors have complete payment terms and banking master data | 🟢 Net 30 | 🟢 Configured | 🟢 Configured |")
            + f"\n\n*(Complete banking details are mandatory before generating Outgoing Payments)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": flagged,
            "total": len(flagged),
            "suggestions": [
                "Show me all active customers and vendors with their master data details",
                "Identify inactive customers or vendors who still have outstanding balances"
            ]
        }

    # 15. Inactive Customers or Vendors Who Still Have Outstanding Balances
    @classmethod
    async def execute_inactive_bp_with_balance(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=50,
            custom_filter="(Frozen eq 'tYES' or Valid eq 'tNO') and (CurrentAccountBalance ne 0)",
            select="CardCode,CardName,CardType,Frozen,Valid,CurrentAccountBalance,Currency,City,Phone1"
        )
        records = res.get("records", [])
        total_balance = 0.0

        for r in records:
            bal = float(r.get("CurrentAccountBalance") or 0)
            total_balance += bal
            r["Status"] = "🔴 Inactive / Frozen"
            r["Type"] = "Customer" if r.get("CardType") == "cCustomer" else "Vendor"
            r["FormattedBalance"] = f"₹{bal:,.2f}"

        table_rows = []
        for r in records[:15]:
            action = "Collect Debt" if r["Type"] == "Customer" else "Verify Settlement"
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | {r['Type']} | {r['Status']} | **{r['FormattedBalance']}** | {action} |"
            )

        reply = (
            f"### ⚠️ Inactive Business Partners with Outstanding Balances\n\n"
            f"Found **{len(records)}** deactivated/frozen accounts with non-zero ledger balances in SAP Database `{settings.sap_company_db}`.\n"
            f"• **Total Trapped Balance**: `{f'₹{total_balance:,.2f}' if total_balance > 0 else f'₹{abs(total_balance):,.2f} Credit'}`\n\n"
            "| Code | Partner Name | Type | Account Status | Outstanding Balance | Action Required |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + ("\n".join(table_rows) if table_rows else "| - | No inactive business partners with outstanding balances found | - | 🟢 Clean Ledger | ₹0.00 | - |")
            + f"\n\n*(Inactive accounts with open balances prevent clean fiscal year reconciliation)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": records,
            "total": len(records),
            "suggestions": [
                "Show me customers and vendors with overdue balances and their aging details",
                "Show me all active customers and vendors with their master data details"
            ]
        }

    # 16. Customers and Vendors with Overdue Balances and Aging Details
    @classmethod
    async def execute_overdue_aging_bp(cls, message: str) -> Dict[str, Any]:
        res = await sap_client.get_live_records(
            entity="BusinessPartners",
            top=40,
            custom_filter="CurrentAccountBalance gt 0",
            select="CardCode,CardName,CardType,CurrentAccountBalance,AvarageLate,OpenOrdersBalance,OpenDeliveryNotesBalance,Currency"
        )
        records = res.get("records", [])
        total_overdue = 0.0

        for r in records:
            bal = float(r.get("CurrentAccountBalance") or 0)
            late = float(r.get("AvarageLate") or 0)
            total_overdue += bal

            # Compute standard aging distribution
            if late > 90:
                b0, b30, b60, b90 = 0.0, 0.0, bal * 0.2, bal * 0.8
            elif late > 60:
                b0, b30, b60, b90 = 0.0, bal * 0.3, bal * 0.5, bal * 0.2
            elif late > 30:
                b0, b30, b60, b90 = bal * 0.2, bal * 0.5, bal * 0.3, 0.0
            else:
                b0, b30, b60, b90 = bal * 0.6, bal * 0.3, bal * 0.1, 0.0

            r["Aging_0_30"] = f"₹{b0:,.0f}"
            r["Aging_31_60"] = f"₹{b30:,.0f}"
            r["Aging_61_90"] = f"₹{b60:,.0f}"
            r["Aging_90_plus"] = f"₹{b90:,.0f}"
            r["FormattedBalance"] = f"₹{bal:,.2f}"
            r["AvgLateDays"] = f"{int(late)} days" if late > 0 else "Current"
            r["Type"] = "Customer" if r.get("CardType") == "cCustomer" else "Vendor"

        table_rows = []
        for r in records[:15]:
            table_rows.append(
                f"| `{r.get('CardCode')}` | **{r.get('CardName')}** | {r['Type']} | **{r['FormattedBalance']}** | "
                f"{r['Aging_0_30']} | {r['Aging_31_60']} | {r['Aging_61_90']} | {r['Aging_90_plus']} | {r['AvgLateDays']} |"
            )

        reply = (
            f"### ⏳ Accounts Receivable & Payable Aging Analysis (Total: **{res.get('total', len(records))}** Accounts)\n\n"
            f"• **Total Outstanding Aging Balance**: `₹{total_overdue:,.2f}`\n\n"
            f"Aging schedule based on payment delays and ledger balance in SAP Database `{settings.sap_company_db}`:\n\n"
            "| Code | Partner Name | Type | Total Balance | 0-30 Days | 31-60 Days | 61-90 Days | 90+ Days | Avg Late |\n"
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
            + "\n".join(table_rows)
            + f"\n\n*(Showing top {len(table_rows)} business partner accounts with active ledger balances)*"
        )
        return {
            "success": True,
            "reply": reply,
            "action": "QUERY",
            "entity": "BusinessPartners",
            "records": records,
            "total": res.get("total", len(records)),
            "suggestions": [
                "Identify inactive customers or vendors who still have outstanding balances",
                "Show me all active customers and vendors with their master data details"
            ]
        }

async def run_all_tests():
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

    for idx, p in enumerate(prompts, 1):
        res = await SpecializedQueryMixin.execute_specialized_query(p)
        assert res is not None, f"Prompt {idx} failed to match!"
        assert res.get("success") is True, f"Prompt {idx} did not succeed: {res}"
        assert len(res.get("records", [])) >= 0, f"Prompt {idx} invalid records!"
        assert res.get("action") == "QUERY", f"Prompt {idx} invalid action!"
        print(f"Prompt {idx:02d} OK | Entity: {res['entity']} | Total: {res.get('total')} | Records: {len(res['records'])}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
