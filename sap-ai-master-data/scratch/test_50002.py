import httpx

for path in ["/b1s/v2", "/b1s/v2/Login", "/b1s/v1", "/b1s/v1/Login", "/b1s"]:
    url = f"http://103.89.45.237:50002{path}"
    try:
        with httpx.Client(timeout=4.0) as client:
            r = client.post(
                url,
                json={"CompanyDB": "CINNTRA_DEMO_NEW", "UserName": "Cinntra1", "Password": "1234"}
            )
            print(f"POST {path} -> {r.status_code}")
            print(r.text[:200])
    except Exception as e:
        print(f"POST {path} -> {e}")
