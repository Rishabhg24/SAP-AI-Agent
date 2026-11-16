import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import json
from app.sap.client import sap_client

async def main():
    async with sap_client._get_http_client() as client:
        await sap_client.auth.login(client)
        res = await sap_client.get("BusinessPartners", params={"$filter": "CardType eq 'cCustomer'", "$top": 2})
        for cust in res.get("value", []):
            print("Cust CardCode:", cust.get("CardCode"))
            print("Cust BPFiscalTaxIDCollection:", json.dumps(cust.get("BPFiscalTaxIDCollection"), indent=2))
            for k, v in cust.items():
                if any(x in k.lower() for x in ["deduct", "tds", "withhold", "taxid"]):
                    print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
