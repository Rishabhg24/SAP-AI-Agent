import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpx
from app.sap.client import sap_client
from app.config import settings

async def main():
    async with sap_client._get_http_client() as client:
        ok, err, *_ = await sap_client.auth.login(client)
        base = settings.sap_service_layer_url.rstrip('/')
        cookies = sap_client.auth.get_cookies()
        
        # 1. States
        res = await client.get(f"{base}/States?$top=100", cookies=cookies)
        print("STATES STATUS:", res.status_code)
        if res.status_code == 200:
            states = res.json().get('value', [])
            print("Total States:", len(states))
            for s in states:
                print(f"  {s.get('Country')} - {s.get('Code')} : {s.get('Name')}")
                
        # 2. Existing BP sample
        res2 = await client.get(f"{base}/BusinessPartners?$top=2", cookies=cookies)
        print("\nBP STATUS:", res2.status_code)
        if res2.status_code == 200:
            bps = res2.json().get('value', [])
            for bp in bps:
                print("BP CardCode:", bp.get('CardCode'))
                print("BP CardName:", bp.get('CardName'))
                print("BP CardType:", bp.get('CardType'))
                print("BP Series:", bp.get('Series'))
                print("BP GroupCode:", bp.get('GroupCode'))
                print("BP PayTermsGrpCode:", bp.get('PayTermsGrpCode'))
                print("BP BPAddresses:", bp.get('BPAddresses'))
                print("BP BPFiscalTaxIDCollection:", bp.get('BPFiscalTaxIDCollection'))

if __name__ == "__main__":
    asyncio.run(main())
