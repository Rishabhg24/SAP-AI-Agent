import asyncio
import json
from app.sap.client import sap_client
from app.models.business_partner import BusinessPartnerCreate
from app.models.item import ItemMasterCreate
from app.models.warehouse import WarehouseCreate

async def test_live_creation():
    # 1. Test Business Partner Creation
    print("Testing Business Partner Creation...")
    bp_data = {
        "CardCode": "C99901",
        "CardName": "Rishabh Tech Global",
        "CardType": "cCustomer",
        "Address": "Plot B-94, MIDC Industrial Area",
        "City": "Mumbai",
        "GSTNo": "27AABCU9603R1ZM",
        "PANNo": "AABCU9603R"
    }
    bp = BusinessPartnerCreate(**bp_data)
    payload = bp.to_service_layer_payload()
    print("BP Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        res = await sap_client.post("BusinessPartners", payload)
        print("BP Created Successfully in SAP:", res.get("CardCode"))
    except Exception as e:
        print("BP Creation Error:", e)

    # 2. Test Item Creation
    print("\nTesting Item Creation...")
    itm_data = {
        "ItemCode": "ITM-9901",
        "ItemName": "Stainless Steel Bolt M12",
        "InventoryUOM": "PCS",
        "ItemsGroupCode": 100,
        "TaxRate": 18
    }
    itm = ItemMasterCreate(**itm_data)
    itm_payload = itm.to_service_layer_payload()
    print("Item Payload:")
    print(json.dumps(itm_payload, indent=2))
    try:
        res_i = await sap_client.post("Items", itm_payload)
        print("Item Created Successfully in SAP:", res_i.get("ItemCode"))
    except Exception as e:
        print("Item Creation Error:", e)

    # 3. Test Warehouse Creation
    print("\nTesting Warehouse Creation...")
    wh_data = {
        "WarehouseCode": "WH99",
        "WarehouseName": "Mumbai Express Hub",
        "Address": "Plot 55 Turbhe",
        "City": "Mumbai",
        "Country": "IN"
    }
    wh = WarehouseCreate(**wh_data)
    wh_payload = wh.to_service_layer_payload()
    print("Warehouse Payload:")
    print(json.dumps(wh_payload, indent=2))
    try:
        res_w = await sap_client.post("Warehouses", wh_payload)
        print("Warehouse Created Successfully in SAP:", res_w.get("WarehouseCode"))
    except Exception as e:
        print("Warehouse Creation Error:", e)

if __name__ == "__main__":
    asyncio.run(test_live_creation())
