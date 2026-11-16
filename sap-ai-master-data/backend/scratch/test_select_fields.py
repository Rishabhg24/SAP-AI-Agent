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

        # Test Items select
        r1 = await c.get(
            f"{url}/Items",
            params={
                "$top": 2,
                "$select": "ItemCode,ItemName,ItemsGroupCode,ChapterID,SalesUnit,PurchaseUnit,BarCode,InventoryItem,SalesItem,PurchaseItem,QuantityOnStock,QuantityOrderedFromVendors,QuantityOrderedByCustomers,MinInventory,MaxInventory,MovingAveragePrice,AvgStdPrice,Valid,Frozen,InventoryUOM,CreateDate,UpdateDate"
            },
            cookies=cookies
        )
        print("Items select status:", r1.status_code)
        if r1.status_code == 200:
            print("Items keys:", list(r1.json().get("value", [{}])[0].keys()))

        # Test BP select
        r2 = await c.get(
            f"{url}/BusinessPartners",
            params={
                "$top": 2,
                "$select": "CardCode,CardName,CardType,FederalTaxID,U_panno,CurrentAccountBalance,Phone1,EmailAddress,Currency,Address,City,ZipCode,Valid,Frozen,PayTermsGrpCode,PeymentMethodCode,HouseBankAccount,HouseBank,AvarageLate,OpenOrdersBalance,OpenDeliveryNotesBalance,CreateDate,UpdateDate"
            },
            cookies=cookies
        )
        print("BP select status:", r2.status_code)
        if r2.status_code == 200:
            print("BP keys:", list(r2.json().get("value", [{}])[0].keys()))

if __name__ == "__main__":
    asyncio.run(main())
