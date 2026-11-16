import sys, os
sys.path.insert(0, os.getcwd())
import asyncio, time
import httpx
from app.main import app

async def test():
    t_now = int(time.time())
    wh_code = f"W{t_now % 10000}"
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=120.0) as client:
        res = await client.post("/api/master-data/bulk-create-direct", json={
            "master_type": "warehouse",
            "confirmed": True,
            "skip_duplicates": False,
            "records": [
                {"WarehouseCode": wh_code}
            ]
        })
        print("Warehouse creation HTTP:", res.status_code)
        summary = res.json().get("data", {}).get("summary", {})
        print("Summary:", summary)
        for r in summary.get("records", []):
            print(f"  {r['code']} | status: {r['status']} | sap_id: {r.get('sap_object_id')} | err: {r.get('error')}")
        assert summary.get("created_count") == 1, "Warehouse should be created!"
        print("Warehouse creation verified successfully!")

if __name__ == "__main__":
    asyncio.run(test())
