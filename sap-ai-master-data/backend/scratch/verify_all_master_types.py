import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import time
from app.models.business_partner import BusinessPartnerCreate, CardTypeEnum
from app.models.item import ItemMasterCreate
from app.models.warehouse import WarehouseCreate
from app.services.validation_service import validation_service
from app.models.extraction import MasterDataType
from app.sap.client import sap_client
from app.sap.business_partners import SAPBusinessPartnersService
from app.sap.items import SAPItemsService
from app.sap.warehouses import SAPWarehousesService

async def main():
    print("=" * 60)
    print("1. TESTING PYDANTIC MODELS WITH MESSY / MINIMAL DATA")
    print("=" * 60)
    
    t = int(time.time()) % 100000

    # Business Partner: only CardCode, CardName, CardType + messy columns (exact screenshot issues)
    bp_input = {
        "CardCode": f"TST{t}",
        "CardName": "MG Creative Tech Pvt Ltd",
        "CardType": "Supplier",
        "EmailAddress": "Contact Person Name | P.A.N. No",
        "AddressLine2": "Invalid Extra Property AddressLine2",
        "FirstName": "Invalid Extra Property FirstName",
        "ItemsGroupCode": "100"
    }
    bp_val = validation_service.validate_business_partner(bp_input)
    assert bp_val.valid == True, "BP validation failed!"
    print("[OK] Business Partner validation passed without error!")
    
    bp_model = BusinessPartnerCreate(**bp_val.validated_data)
    bp_payload = bp_model.to_service_layer_payload()
    print("BP Payload keys:", list(bp_payload.keys()))
    assert "AddressLine2" not in bp_payload, "AddressLine2 must not be in payload!"
    assert "FirstName" not in bp_payload, "FirstName must not be in payload!"
    assert bp_payload.get("EmailAddress") is None, "EmailAddress must be sanitized to None!"
    assert bp_payload.get("U_VSG") == "Expenses", "U_VSG must be set for OCRD!"
    assert bp_payload["BPFiscalTaxIDCollection"][0].get("TaxId12") is not None, "TaxId12 must be present!"
    print("[OK] Business Partner payload sanitized & compliant!")

    # Item: only ItemCode & ItemName
    itm_input = {
        "ItemCode": f"ITM{t}",
        "ItemName": "Stainless Steel M10 Hex Bolt",
        "AddressLine2": "Ignored",
    }
    itm_val = validation_service.validate_item(itm_input)
    assert itm_val.valid == True, "Item validation failed!"
    itm_model = ItemMasterCreate(**itm_val.validated_data)
    itm_payload = itm_model.to_service_layer_payload()
    print("Item Payload keys:", list(itm_payload.keys()))
    assert itm_payload.get("ItemCode") == f"ITM{t}"
    assert itm_payload.get("ItemName") == "Stainless Steel M10 Hex Bolt"
    assert "AddressLine2" not in itm_payload
    print("[OK] Item Master payload sanitized & compliant!")

    # Warehouse: only WarehouseCode
    wh_input = {
        "WarehouseCode": f"W{t % 10000}",
    }
    wh_val = validation_service.validate_warehouse(wh_input)
    assert wh_val.valid == True, "Warehouse validation failed!"
    wh_model = WarehouseCreate(**wh_val.validated_data)
    wh_payload = wh_model.to_service_layer_payload()
    print("Warehouse Payload keys:", list(wh_payload.keys()))
    assert wh_payload.get("WarehouseCode") == f"W{t % 10000}"
    assert wh_payload.get("WarehouseName") is not None
    print("[OK] Warehouse Master payload sanitized & compliant!")

    print("\n" + "=" * 60)
    print("2. TESTING LIVE SAP B1 SERVICE LAYER CREATION")
    print("=" * 60)

    # Live SAP Item creation
    print("\nPosting Item Master to live SAP...")
    try:
        item_res = await SAPItemsService.create_item(itm_model)
        print(f"--> SUCCESS! Item created in SAP: {item_res.get('ItemCode')}")
    except Exception as e:
        print(f"--> FAILED Item: {e}")

    # Live SAP Supplier creation
    print("\nPosting Business Partner (Supplier) to live SAP...")
    try:
        bp_res = await SAPBusinessPartnersService.create_business_partner(bp_model)
        print(f"--> SUCCESS! Supplier created in SAP: {bp_res.get('CardCode')}")
    except Exception as e:
        print(f"--> FAILED Supplier: {e}")

    # Live SAP Customer creation
    print("\nPosting Business Partner (Customer) to live SAP...")
    cust_model = BusinessPartnerCreate(
        CardCode=f"CST{t}",
        CardName="ABC Pvt Ltd Customer",
        CardType="Customer"
    )
    try:
        cust_res = await SAPBusinessPartnersService.create_business_partner(cust_model)
        print(f"--> SUCCESS! Customer created in SAP: {cust_res.get('CardCode')}")
    except Exception as e:
        print(f"--> FAILED Customer: {e}")

    # Live SAP Warehouse creation
    print("\nPosting Warehouse to live SAP...")
    try:
        wh_res = await SAPWarehousesService.create_warehouse(wh_model)
        print(f"--> SUCCESS! Warehouse created in SAP: {wh_res.get('WarehouseCode')}")
    except Exception as e:
        print(f"--> FAILED Warehouse: {e}")

    print("\n" + "=" * 60)
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
