import asyncio
import json
from app.sap.client import sap_client
from app.config import settings

async def check():
    async with sap_client._get_http_client() as client:
        ok, err, *_ = await sap_client.auth.login(client)
        print("Login:", ok, err)
        if not ok:
            return
        cookies = sap_client.auth.get_cookies()
        base = settings.sap_service_layer_url.rstrip("/")

        # Try fetching without params or with dict params
        print("\n--- SAMPLE BUSINESS PARTNERS ---")
        r = await client.get(f"{base}/BusinessPartners", params={"$top": 2}, cookies=cookies)
        if r.status_code == 200:
            for bp in r.json().get("value", []):
                print("CardCode:", bp.get("CardCode"), "CardName:", bp.get("CardName"), "CardType:", bp.get("CardType"), "VatGroup:", bp.get("VatGroup"), "Series:", bp.get("Series"), "Currency:", bp.get("Currency"))
                print("  BPAddresses:", bp.get("BPAddresses"))
        else:
            print(r.status_code, r.text)

        print("\n--- SAMPLE ITEMS ---")
        r = await client.get(f"{base}/Items", params={"$top": 2}, cookies=cookies)
        if r.status_code == 200:
            for it in r.json().get("value", []):
                print("ItemCode:", it.get("ItemCode"), "ItemName:", it.get("ItemName"), "ItemsGroupCode:", it.get("ItemsGroupCode"), "SalesVATGroup:", it.get("SalesVATGroup"), "PurchaseVATGroup:", it.get("PurchaseVATGroup"), "InventoryUOM:", it.get("InventoryUOM"))
        else:
            print(r.status_code, r.text)

        print("\n--- SAMPLE WAREHOUSES ---")
        r = await client.get(f"{base}/Warehouses", params={"$top": 3}, cookies=cookies)
        if r.status_code == 200:
            for wh in r.json().get("value", []):
                print("WarehouseCode:", wh.get("WarehouseCode"), "WarehouseName:", wh.get("WarehouseName"), "Street:", wh.get("Street"), "City:", wh.get("City"), "State:", wh.get("State"), "Country:", wh.get("Country"))
        else:
            print(r.status_code, r.text)

        print("\n--- VAT GROUPS ---")
        r = await client.get(f"{base}/VatGroups", params={"$top": 10}, cookies=cookies)
        if r.status_code == 200:
            for vg in r.json().get("value", []):
                print("VatGroup Code:", vg.get("Code"), "Name:", vg.get("Name"), "Category:", vg.get("Category"))
        else:
            print(r.status_code, r.text)

        print("\n--- STATES ---")
        r = await client.get(f"{base}/States", params={"$top": 10}, cookies=cookies)
        if r.status_code == 200:
            for st in r.json().get("value", []):
                print("State Code:", st.get("Code"), "Country:", st.get("Country"), "Name:", st.get("Name"))
        else:
            print(r.status_code, r.text)

        print("\n--- ITEM GROUPS ---")
        r = await client.get(f"{base}/ItemGroups", params={"$top": 10}, cookies=cookies)
        if r.status_code == 200:
            for ig in r.json().get("value", []):
                print("Number:", ig.get("Number"), "GroupName:", ig.get("GroupName"))
        else:
            print(r.status_code, r.text)

asyncio.run(check())
