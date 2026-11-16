import asyncio
from app.sap.client import sap_client

async def test():
    res = await sap_client.get('BusinessPartners', params={"$top": 2})
    print("RES VALUE:", res.get("value"))

if __name__ == "__main__":
    asyncio.run(test())
