"""
Webserver Launcher for SAP AI Master Data Automation Platform.
Dynamically reads host, port, reload, and log level from active configuration (connections.json / .env).
"""
import os
import sys
import uvicorn
from app.config import settings, get_connections_file_path
from app.utils.logging import logger

def start_server():
    active_cfg = get_connections_file_path()
    active_host = os.environ.get("HOST", settings.host)
    active_port = int(os.environ.get("PORT", settings.port))

    print("=" * 60)
    print("SAP AI Master Data Automation Platform - Web Server")
    print("=" * 60)
    print(f"Dynamic Config File: {active_cfg}")
    print(f"Web Server Host:     {active_host}")
    print(f"Web Server Port:     {active_port}")
    print(f"Frontend Client URL: {settings.frontend_url}")
    print(f"Allowed CORS Origins: {settings.parsed_cors_origins}")
    print(f"Environment:         {settings.environment}")
    print(f"Log Level:           {settings.log_level}")
    print("=" * 60)
    print(f"Starting server on http://{active_host}:{active_port} ...")

    uvicorn.run(
        "app.main:app",
        host=active_host,
        port=active_port,
        reload=settings.environment.lower() == "development",
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    start_server()
