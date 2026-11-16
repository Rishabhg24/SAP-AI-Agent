import asyncio
import json
from app.sap.client import sap_client

async def test_fixed_items_warehouses():
    # 1. Test Fixed Item Creation
    print("Testing Fixed Item Creation...")
    itm_payload = {
        "ItemCode": "ITM-9902",
        "ItemName": "Stainless Steel Bolt M12",
        "ItemsGroupCode": 100,
        "InventoryItem": "tYES",
        "SalesItem": "tYES",
        "PurchaseItem": "tYES",
        "InventoryUOM": "PCS",
        "ManageSerialNumbers": "tNO",
        "ManageBatchNumbers": "tNO",
        "ItemClass": "itcMaterial"
    }
    try:
        res_i = await sap_client.post("Items", itm_payload)
        print("Item Created Successfully in SAP:", res_i.get("ItemCode"))
    except Exception as e:
        print("Item Creation Error:", e)

    # 2. Test Fixed Warehouse Creation
    print("\nTesting Fixed Warehouse Creation...")
    wh_payload = {
        "WarehouseCode": "WH99",
        "WarehouseName": "Mumbai Express Hub",
        "Inactive": "tNO",
        "EnableBinLocations": "tNO",
        "Street": "Plot 55 Turbhe",
        "City": "Mumbai",
        "State": "MH",
        "Country": "IN"
    }
    try:
        res_w = await sap_client.post("Warehouses", wh_payload)
        print("Warehouse Created Successfully in SAP:", res_w.get("WarehouseCode"))
    except Exception as e:
        print("Warehouse Creation Error:", e)

if __name__ == "__main__":
    asyncio.run(test_fixed_items_warehouses())
