import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio, time
from app.sap.client import sap_client

async def test_pan(pan_val):
    t = int(time.time() * 100) % 100000
    card_code = f"CS{t}"
    payload = {
        "CardCode": card_code,
        "CardName": f"Cust {card_code}",
        "CardType": "cCustomer",
        "GroupCode": 100,
        "PayTermsGrpCode": 2,
        "Currency": "INR",
        "Series": 86,
        "U_VSG": "Expenses",
        "U_panno": pan_val,
        "BPFiscalTaxIDCollection": [
            {"Address": "", "TaxId0": pan_val, "AddrType": "bo_ShipTo", "TaxId12": f"{card_code}/DEF"},
            {"Address": "Bill To", "TaxId0": pan_val, "AddrType": "bo_BillTo", "TaxId12": f"{card_code}/BILL"},
            {"Address": "Ship To", "TaxId0": pan_val, "AddrType": "bo_ShipTo", "TaxId12": f"{card_code}/SHIP"}
        ]
    }
    try:
        res = await sap_client.post("BusinessPartners", payload)
        print(f"PAN '{pan_val}': SUCCESS -> {res.get('CardCode')}")
    except Exception as e:
        print(f"PAN '{pan_val}': FAILED -> {e}")

async def main():
    await test_pan("ABCDE1234F")
    await test_pan("PANNOTAVBL")

if __name__ == "__main__":
    asyncio.run(main())
