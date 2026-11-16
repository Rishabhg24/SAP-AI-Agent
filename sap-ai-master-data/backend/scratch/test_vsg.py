import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import time
from app.sap.client import sap_client

async def main():
    t = int(time.time()) % 100000
    card_code = f"CS{t}"
    pan = "ABCDE1234F"
    for vsg in ["Expenses", "Raw Material"]:
        payload = {
            "CardCode": card_code + vsg[:2],
            "CardName": f"Customer {t} {vsg}",
            "CardType": "cCustomer",
            "GroupCode": 100,
            "PayTermsGrpCode": 2,
            "Currency": "INR",
            "Series": 86,
            "U_VSG": vsg,
            "U_panno": pan,
            "BPFiscalTaxIDCollection": [
                {"Address": "", "TaxId0": pan, "AddrType": "bo_ShipTo", "TaxId12": f"{card_code}/DEF"},
                {"Address": "Bill To", "TaxId0": pan, "AddrType": "bo_BillTo", "TaxId12": f"{card_code}/BILL"},
                {"Address": "Ship To", "TaxId0": pan, "AddrType": "bo_ShipTo", "TaxId12": f"{card_code}/SHIP"}
            ]
        }
        try:
            res = await sap_client.post("BusinessPartners", payload)
            print(f"VSG '{vsg}': SUCCESS -> {res.get('CardCode')}")
        except Exception as e:
            print(f"VSG '{vsg}': FAILED -> {e}")

if __name__ == "__main__":
    asyncio.run(main())
