import asyncio
import sys
from app.sap.client import sap_client
from app.config import settings

async def main():
    async with sap_client._get_http_client() as client:
        ok, err, *_ = await sap_client.auth.login(client)
        print("Login ok:", ok, "err:", err)
        if ok:
            url = f"{settings.sap_service_layer_url.rstrip('/')}/Items"
            r1 = await client.get(url, params={"$top": 3, "$select": "ItemCode,CreateDate"}, cookies=sap_client.auth.get_cookies())
            print("Plain status:", r1.status_code, r1.text[:200])

            r2 = await client.get(url, params={"$top": 3, "$select": "ItemCode,CreateDate", "$filter": "CreateDate ge '2026-01-01'"}, cookies=sap_client.auth.get_cookies())
            print("Quoted date status:", r2.status_code, r2.text[:200])

            r3 = await client.get(url, params={"$top": 3, "$select": "ItemCode,CreateDate", "$filter": "CreateDate ge 2026-01-01"}, cookies=sap_client.auth.get_cookies())
            print("Unquoted date status:", r3.status_code, r3.text[:200])

asyncio.run(main())
