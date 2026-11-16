import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import time
from app.sap.client import sap_client

async def main():
    t = int(time.time()) % 100000
    card_code = f"CST{t}"
    pan = "ABCDE1234F"
    payload = {
        "CardCode": card_code,
        "CardName": f"Customer {t}",
        "CardType": "cCustomer",
        "GroupCode": 100,
        "PayTermsGrpCode": 2,
        "Currency": "INR",
        "Series": 86,
        "U_VSG": "Expenses",
        "U_panno": pan,
        "BPFiscalTaxIDCollection": [
            {"Address": "", "TaxId0": pan, "AddrType": "bo_ShipTo", "TaxId12": f"{card_code}/DEFAULT"},
            {"Address": "Bill To", "TaxId0": pan, "AddrType": "bo_BillTo", "TaxId12": f"{card_code}/BILL"},
            {"Address": "Ship To", "TaxId0": pan, "AddrType": "bo_ShipTo", "TaxId12": f"{card_code}/SHIP"}
        ]
    }
    try:
        res = await sap_client.post("BusinessPartners", payload)
        print("SUCCESS! Created Customer:", res.get("CardCode"))
    except Exception as e:
        print("FAILED:", e)

if __name__ == "__main__":
    asyncio.run(main())
