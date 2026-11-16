import ssl, socket, httpx

# 1. Check SSL Certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with socket.create_connection(('103.89.45.237', 50000), timeout=5.0) as sock:
    with ctx.wrap_socket(sock) as ssock:
        cert = ssock.getpeercert(binary_form=True)
        # get text cert
        import ssl
        cert_dict = ssl.DER_cert_to_PEM_cert(cert)
        print("Certificate PEM:")
        print(cert_dict[:200])

# 2. Check HTTP headers
with httpx.Client(verify=False, timeout=5.0) as client:
    r = client.get('https://103.89.45.237:50000/', headers={'User-Agent': 'Mozilla/5.0'})
    print('Status:', r.status_code)
    print('Server headers:', dict(r.headers))
    print('Server body:', r.text[:300])
