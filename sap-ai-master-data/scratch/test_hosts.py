import httpx

for host in ["CINNTRA-DEMO", "CINNTRA-DEMO:50000", "localhost", "127.0.0.1", "103.89.45.237"]:
    for path in ["/b1s/v2", "/b1s/v2/Login"]:
        url = f"https://103.89.45.237:50000{path}"
        try:
            with httpx.Client(verify=False, timeout=12.0) as client:
                r = client.post(
                    url,
                    json={"CompanyDB": "CINNTRA_DEMO_NEW", "UserName": "Cinntra1", "Password": "1234"},
                    headers={"Host": host, "User-Agent": "SAP-B1-Client"}
                )
                print(f"Host: {host:20} Path: {path} -> {r.status_code}")
                if r.status_code != 403:
                    print(r.text[:200])
        except Exception as e:
            print(f"Host: {host:20} Path: {path} -> {type(e).__name__}: {e}")
