import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from app.sap.client import sap_client
from app.config import settings

STATE_CODE_MAP = {
    "DELHI": "DL", "DL": "DL",
    "MAHARASHTRA": "MH", "MH": "MH",
    "KARNATAKA": "KA", "KA": "KA",
    "TAMIL NADU": "TN", "TAMILNADU": "TN", "TN": "TN",
    "UTTAR PRADESH": "UP", "UP": "UP",
    "GUJARAT": "GJ", "GJ": "GJ",
    "HARYANA": "HR", "HR": "HR",
    "WEST BENGAL": "WB", "WB": "WB",
    "RAJASTHAN": "RJ", "RJ": "RJ",
    "TELANGANA": "TG", "TG": "TG",
    "ANDHRA PRADESH": "AP", "AP": "AP",
    "MADHYA PRADESH": "MP", "MP": "MP",
    "PUNJAB": "PB", "PB": "PB",
    "UTTARAKHAND": "UK", "UK": "UK",
}

async def test():
    async with sap_client._get_http_client() as client:
        await sap_client.auth.login(client)
        base = settings.sap_service_layer_url.rstrip("/")

        records = [
            {
                "CardCode": "CUST001",
                "CardName": "ABC Pvt Ltd",
                "CardType": "cCustomer",
                "Address": "123 Main St",
                "City": "Delhi",
                "State": "Delhi",
                "ZipCode": "110001"
            },
            {
                "CardCode": "CUST002",
                "CardName": "XYZ Ltd",
                "CardType": "cCustomer",
                "Address": "45 Park Road",
                "City": "Mumbai",
                "State": "Maharashtra",
                "ZipCode": "400001"
            }
        ]

        for r in records:
            st = STATE_CODE_MAP.get(r["State"].upper(), "DL")
            p = {
                "CardCode": r["CardCode"],
                "CardName": r["CardName"],
                "CardType": "cCustomer",
                "GroupCode": 100,
                "PayTermsGrpCode": -1,
                "Series": 86,
                "U_VSG": "Expenses",
                "BPAddresses": [
                    {
                        "AddressName": "Bill To",
                        "Street": r["Address"],
                        "City": r["City"],
                        "ZipCode": str(r["ZipCode"]),
                        "Country": "IN",
                        "State": st,
                        "AddressType": "bo_BillTo"
                    },
                    {
                        "AddressName": "Ship To",
                        "Street": r["Address"],
                        "City": r["City"],
                        "ZipCode": str(r["ZipCode"]),
                        "Country": "IN",
                        "State": st,
                        "AddressType": "bo_ShipTo"
                    }
                ],
                "BPFiscalTaxIDCollection": [
                    {"Address": "", "TaxId0": "ABCDE1234F", "AddrType": "bo_ShipTo", "TaxId12": f"{r['CardCode']}/DEFAULT"},
                    {"Address": "Bill To", "TaxId0": "ABCDE1234F", "AddrType": "bo_BillTo", "TaxId12": f"{r['CardCode']}/BILL"},
                    {"Address": "Ship To", "TaxId0": "ABCDE1234F", "AddrType": "bo_ShipTo", "TaxId12": f"{r['CardCode']}/SHIP"}
                ]
            }
            res = await client.post(f"{base}/BusinessPartners", json=p, cookies=sap_client.auth.get_cookies())
            print(f"Creating {r['CardCode']}: status {res.status_code}")
            if res.status_code != 201:
                print("Error:", res.text)
            else:
                print("Success! Created:", res.json().get("CardCode"))

if __name__ == "__main__":
    asyncio.run(test())
