import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio, time
import httpx
from app.main import app

async def main():
    t_now = int(time.time())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Item Master: only ItemCode & ItemName
        print("\n=== Testing Direct Bulk: Item Master ===")
        res = await client.post("/api/master-data/bulk-create-direct", json={
            "master_type": "item",
            "confirmed": True,
            "skip_duplicates": False,
            "records": [
                {"ItemCode": f"ITM{t_now % 100000}", "ItemName": "High Tensile Steel Bolt M12"}
            ]
        })
        print("Status:", res.status_code)
        resp = res.json()
        summary = resp.get("data", {}).get("summary", {})
        print("Created:", summary.get("created_count"), "Failed:", summary.get("failed_count"))
        for r in summary.get("records", []):
            print(f"  Record: {r['code']} | Status: {r['status']} | SAP ID: {r.get('sap_object_id')} | Error: {r.get('error')}")
        assert summary.get("created_count") == 1, "Item should be created!"

        # 2. Business Partner: messy columns & invalid email header (exact issue from user screenshot)
        print("\n=== Testing Direct Bulk: Business Partner (Messy columns & invalid email) ===")
        res = await client.post("/api/master-data/bulk-create-direct", json={
            "master_type": "business_partner",
            "confirmed": True,
            "skip_duplicates": False,
            "records": [
                {
                    "CardCode": f"V{t_now % 100000}",
                    "CardName": "MG Creative Tech Corp",
                    "CardType": "Supplier",
                    "EmailAddress": "Contact Person Name | P.A.N. No",
                    "AddressLine2": "Invalid Extra Property AddressLine2",
                    "FirstName": "Invalid Extra Property FirstName",
                    "ItemsGroupCode": "100"
                }
            ]
        })
        print("Status:", res.status_code)
        resp = res.json()
        summary = resp.get("data", {}).get("summary", {})
        print("Created:", summary.get("created_count"), "Failed:", summary.get("failed_count"))
        for r in summary.get("records", []):
            print(f"  Record: {r['code']} | Status: {r['status']} | SAP ID: {r.get('sap_object_id')} | Error: {r.get('error')}")
        assert summary.get("created_count") == 1, "Business Partner should be created!"

        # 3. Customer with only code & name
        print("\n=== Testing Direct Bulk: Customer (Only code & name) ===")
        res = await client.post("/api/master-data/bulk-create-direct", json={
            "master_type": "business_partner",
            "confirmed": True,
            "skip_duplicates": False,
            "records": [
                {
                    "CardCode": f"C{t_now % 100000}",
                    "CardName": "ABC Pvt Ltd Direct",
                    "CardType": "Customer"
                }
            ]
        })
        print("Status:", res.status_code)
        resp = res.json()
        summary = resp.get("data", {}).get("summary", {})
        print("Created:", summary.get("created_count"), "Failed:", summary.get("failed_count"))
        for r in summary.get("records", []):
            print(f"  Record: {r['code']} | Status: {r['status']} | SAP ID: {r.get('sap_object_id')} | Error: {r.get('error')}")
        assert summary.get("created_count") == 1, "Customer should be created!"

    print("\n>>> ALL API ENDPOINT BULK CREATION TESTS PASSED! <<<")

if __name__ == "__main__":
    asyncio.run(main())
