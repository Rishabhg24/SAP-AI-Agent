import httpx

for host in ["CINNTRA-DEMO", "cinntra-demo", "103.89.45.237:50000", "103.89.45.237"]:
    for prefix in ["https://103.89.45.237:50000", "https://103.89.45.237:50001"]:
        try:
            with httpx.Client(verify=False, timeout=3.0) as client:
                r = client.post(
                    f"{prefix}/b1s/v2/Login",
                    json={"CompanyDB": "CINNTRA_DEMO_NEW", "UserName": "Cinntra1", "Password": "1234"},
                    headers={"Host": host, "Accept": "application/json", "Content-Type": "application/json"}
                )
                print(f"{prefix} with Host={host} -> {r.status_code}")
                if r.status_code != 403:
                    print(r.text[:200])
        except Exception as e:
            print(f"{prefix} with Host={host} -> {type(e).__name__}")
