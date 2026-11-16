import socket

for port in [50000, 50001, 50002]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect(('103.89.45.237', port))
        # Send raw HTTP GET
        req = b"GET / HTTP/1.0\r\nHost: 103.89.45.237\r\n\r\n"
        s.sendall(req)
        resp = s.recv(1024)
        print(f"Port {port} raw HTTP response:")
        print(resp.decode('latin1', errors='ignore')[:300])
    except Exception as e:
        print(f"Port {port} error: {e}")
    finally:
        s.close()
