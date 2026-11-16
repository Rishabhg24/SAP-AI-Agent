import asyncio
import json
from app.sap.client import sap_client

async def main():
    async with sap_client._get_http_client() as client:
        ok, err, *_ = await sap_client.auth.login(client)
        print("Login:", ok)
        
        # 1. Fetch one Item
        r_item = await client.get(
            f"{sap_client.auth.service_layer_url.rstrip('/')}/Items?$top=1",
            cookies=sap_client.auth.get_cookies()
        )
        if r_item.status_code == 200:
            val = r_item.json().get("value", [])
            if val:
                item = val[0]
                print("\n--- ITEM FIELDS ---")
                for k in sorted(item.keys()):
                    if any(x in k.lower() for x in ["stock", "uom", "unit", "qty", "quantity", "valid", "frozen", "active", "min", "max", "ordered", "committed", "create", "hsn", "chapter"]):
                        print(f"  {k}: {item[k]}")
                print("\nItemWarehouseInfoCollection length:", len(item.get("ItemWarehouseInfoCollection", [])))
                if item.get("ItemWarehouseInfoCollection"):
                    print("Sample WH Info:", json.dumps(item["ItemWarehouseInfoCollection"][0], indent=2))
        
        # 2. Fetch one BusinessPartner
        r_bp = await client.get(
            f"{sap_client.auth.service_layer_url.rstrip('/')}/BusinessPartners?$top=1",
            cookies=sap_client.auth.get_cookies()
        )
        if r_bp.status_code == 200:
            val = r_bp.json().get("value", [])
            if val:
                bp = val[0]
                print("\n--- BP FIELDS ---")
                for k in sorted(bp.keys()):
                    if any(x in k.lower() for x in ["valid", "frozen", "balance", "create", "user", "tax", "gst", "pan", "pay", "bank", "term", "currency"]):
                        print(f"  {k}: {bp[k]}")
                print("\nBPFiscalTaxIDCollection:", bp.get("BPFiscalTaxIDCollection"))
                print("BPPaymentMethods:", bp.get("BPPaymentMethods"))
                print("BPBankAccounts:", bp.get("BPBankAccounts"))

if __name__ == "__main__":
    asyncio.run(main())
