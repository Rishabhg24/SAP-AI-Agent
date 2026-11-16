import httpx

url = "http://103.89.45.237:50001/b1s/v2/Login"
for host in [None, "CINNTRA-DEMO:50001", "103.89.45.237:50001"]:
    headers = {"Host": host} if host else {}
    try:
        with httpx.Client(timeout=3.0) as client:
            r = client.post(url, json={"CompanyDB": "CINNTRA_DEMO_NEW", "UserName": "Cinntra1", "Password": "1234"}, headers=headers)
            print(f"Host: {host} -> {r.status_code}")
    except Exception as e:
        print(f"Host: {host} -> {type(e).__name__}: {e}")
