import asyncio
import json
from app.sap.client import sap_client
from app.config import settings

async def test_all_in_states():
    async with sap_client._get_http_client() as client:
        ok, err, *_ = await sap_client.auth.login(client)
        url_st = f"{settings.sap_service_layer_url.rstrip('/')}/States"
        resp_st = await client.get(
            url_st,
            params={"$filter": "Country eq 'IN'", "$top": 50},
            cookies=sap_client.auth.get_cookies()
        )
        if resp_st.status_code == 200:
            states = resp_st.json().get("value", [])
            state_map = {s.get("GSTCode"): s.get("Code") for s in states}
            print("STATE MAP (GSTCode -> StateCode):")
            print(json.dumps(state_map, indent=2))
            names_map = {s.get("Name").lower(): s.get("Code") for s in states if s.get("Name")}
            print("STATE NAME MAP:", json.dumps(names_map, indent=2))

if __name__ == "__main__":
    asyncio.run(test_all_in_states())
