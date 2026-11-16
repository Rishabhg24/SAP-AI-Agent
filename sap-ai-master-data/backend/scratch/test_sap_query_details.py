import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import json
from app.sap.client import sap_client
from app.config import settings

async def main():
    async with sap_client._get_http_client() as client:
        await sap_client.auth.login(client)
        cookies = sap_client.auth.get_cookies()
        url = settings.sap_service_layer_url.rstrip("/")

        tests = [
            # 1. Missing HSN or Inventory UoM
            ("Items - Missing HSN or UoM", f"{url}/Items?$filter=(ChapterID eq -1 or ChapterID eq null or InventoryUOM eq null)&$top=2&$select=ItemCode,ItemName,ChapterID,InventoryUOM"),
            # 2. Inactive items with stock
            ("Items - Inactive with stock", f"{url}/Items?$filter=Frozen eq 'tYES' and QuantityOnStock gt 0&$top=2&$select=ItemCode,ItemName,Frozen,QuantityOnStock"),
            # 3. Warehouse stock
            ("Items - Warehouse stock", f"{url}/Items?$filter=QuantityOnStock gt 0&$top=2&$select=ItemCode,ItemName,QuantityOnStock,ItemWarehouseInfoCollection"),
            # 4. Ordered and committed
            ("Items - Ordered & Committed", f"{url}/Items?$filter=QuantityOrderedFromVendors gt 0 or QuantityOrderedByCustomers gt 0&$top=2&$select=ItemCode,ItemName,QuantityOrderedFromVendors,QuantityOrderedByCustomers"),
            # 5. Active Customers & Vendors
            ("BP - Active Customers & Vendors", f"{url}/BusinessPartners?$filter=Frozen eq 'tNO'&$top=2&$select=CardCode,CardName,CardType,FederalTaxID,CurrentAccountBalance"),
            # 6. Inactive BPs with outstanding balance
            ("BP - Inactive with balance", f"{url}/BusinessPartners?$filter=Frozen eq 'tYES' and CurrentAccountBalance ne 0&$top=2&$select=CardCode,CardName,Frozen,CurrentAccountBalance"),
            # 7. Vendors missing bank / payment terms
            ("BP - Vendors missing terms", f"{url}/BusinessPartners?$filter=CardType eq 'cSupplier' and (PayTermsGrpCode eq null or PayTermsGrpCode eq -1 or PeymentMethodCode eq null)&$top=2&$select=CardCode,CardName,CardType,PayTermsGrpCode,PeymentMethodCode"),
            # 8. Overdue / Balance BPs
            ("BP - Overdue balance", f"{url}/BusinessPartners?$filter=CurrentAccountBalance gt 0&$top=2&$select=CardCode,CardName,CurrentAccountBalance,AvarageLate,OpenOrdersBalance"),
        ]

        for name, req_url in tests:
            try:
                resp = await client.get(req_url, cookies=cookies)
                vals = resp.json().get("value", []) if resp.status_code == 200 else resp.text[:200]
                print(f"=== {name} (Status: {resp.status_code}, Count: {len(vals) if isinstance(vals, list) else 0}) ===")
                if isinstance(vals, list) and vals:
                    print(json.dumps(vals[0], indent=2))
            except Exception as e:
                print(f"Error on {name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
