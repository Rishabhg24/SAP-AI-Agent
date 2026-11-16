import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from app.sap.client import sap_client
from app.config import settings

async def main():
    async with sap_client._get_http_client() as c:
        await sap_client.auth.login(c)
        url = settings.sap_service_layer_url.rstrip("/")
        cookies = sap_client.auth.get_cookies()

        # Test Items with warehouse collection
        r = await c.get(
            f"{url}/Items",
            params={
                "$filter": "QuantityOnStock gt 0",
                "$top": 5,
                "$select": "ItemCode,ItemName,QuantityOnStock,InventoryUOM,ItemWarehouseInfoCollection"
            },
            cookies=cookies
        )
        print("Warehouse collection status:", r.status_code)
        if r.status_code == 200:
            for item in r.json().get("value", []):
                print(f"Item {item['ItemCode']} - Stock: {item['QuantityOnStock']} {item.get('InventoryUOM')}")
                wh_with_stock = [w for w in item.get("ItemWarehouseInfoCollection", []) if w.get("InStock", 0) > 0]
                for wh in wh_with_stock[:3]:
                    print(f"  WH {wh.get('WarehouseCode')}: {wh.get('InStock')}")

if __name__ == "__main__":
    asyncio.run(main())
