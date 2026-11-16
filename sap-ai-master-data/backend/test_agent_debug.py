import asyncio
import json
from app.sap.client import sap_client
from app.config import settings

async def test_states():
    async with sap_client._get_http_client() as client:
        ok, err, *_ = await sap_client.auth.login(client)
        print("Login ok:", ok, "db:", settings.sap_company_db)
        
        # Query real BP
        url = f"{settings.sap_service_layer_url.rstrip('/')}/BusinessPartners"
        resp = await client.get(
            url,
            params={"$top": 2, "$select": "CardCode,CardName,CardType,BPAddresses,BPFiscalTaxIDCollection,Series,GroupCode,PayTermsGrpCode"},
            cookies=sap_client.auth.get_cookies()
        )
        print("Real BP HTTP:", resp.status_code)
        if resp.status_code == 200:
            print("BP DATA:")
            print(json.dumps(resp.json(), indent=2))
        else:
            print("BP ERR:", resp.text)
            
        # Query real States
        url_st = f"{settings.sap_service_layer_url.rstrip('/')}/States"
        resp_st = await client.get(
            url_st,
            params={"$top": 15},
            cookies=sap_client.auth.get_cookies()
        )
        print("States HTTP:", resp_st.status_code)
        if resp_st.status_code == 200:
            print("STATES DATA:")
            print(json.dumps(resp_st.json(), indent=2))
        else:
            print("STATES ERR:", resp_st.text)

if __name__ == "__main__":
    asyncio.run(test_states())
