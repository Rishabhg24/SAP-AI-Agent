import asyncio
from app.sap.client import sap_client

async def test():
    async with sap_client._get_http_client() as client:
        await sap_client.auth.login(client)
        # Check existing customers
        res = await sap_client.get('BusinessPartners', params={"$filter": "CardType eq 'cCustomer'", "$top": 2})
        for bp in res.get("value", []):
            print("Cust CardCode:", bp.get("CardCode"), "Series:", bp.get("Series"), "PayTermsGrpCode:", bp.get("PayTermsGrpCode"), "GroupCode:", bp.get("GroupCode"))

        # Test creating customer with PAN
        test_cust = {
            "CardCode": "CUST_TEST_99",
            "CardName": "Test Customer NinetyNine",
            "CardType": "cCustomer",
            "Series": 86,
            "GroupCode": 100,
            "PayTermsGrpCode": 2,
            "Currency": "INR",
            "U_VSG": "Expenses",
            "U_panno": "ABCDE1234F",
            "BPFiscalTaxIDCollection": [
                {"Address": "", "TaxId0": "ABCDE1234F", "AddrType": "bo_ShipTo"},
                {"Address": "Bill To", "TaxId0": "ABCDE1234F", "AddrType": "bo_BillTo"},
                {"Address": "Ship To", "TaxId0": "ABCDE1234F", "AddrType": "bo_ShipTo"}
            ]
        }
        res_c = await sap_client.post("BusinessPartners", test_cust)
        print("Customer creation result:", res_c.get("CardCode"))

if __name__ == "__main__":
    asyncio.run(test())
