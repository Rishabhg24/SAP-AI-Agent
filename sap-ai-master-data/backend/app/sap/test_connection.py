"""
CLI test command: python -m app.sap.test_connection
Tests connectivity and authentication to SAP Business One Service Layer safely without printing passwords.
"""
import asyncio
import sys
from app.config import settings
from app.sap.client import sap_client

async def main():
    print("==================================================")
    print("SAP BUSINESS ONE SERVICE LAYER CONNECTION TEST")
    print("==================================================")
    print("Connecting to SAP...")
    print(f"Service Layer URL: {settings.sap_service_layer_url}")
    print(f"Company DB:        {settings.sap_company_db}")
    print(f"SAP Username:      {settings.sap_username}")
    print(f"SAP Password:      ***REDACTED***")
    print("Authenticating...")

    health = await sap_client.check_health()
    status = health.get("status")
    message = health.get("message")
    
    print("--------------------------------------------------")
    print(f"Company DB: configured ({settings.sap_company_db})")
    
    if status == "CONNECTED":
        print("Service Layer: reachable")
        print("Login: successful")
        print("Status: READY FOR PRODUCTION MASTER DATA")
        print("==================================================")
        sys.exit(0)
    elif status == "DEVELOPMENT_SIMULATION":
        print("Service Layer: Simulated (Development Mode)")
        print("Login: Simulated Sandbox Active")
        print(f"Note: {message}")
        print("Status: READY FOR LOCAL DEVELOPMENT & PIPELINE TESTING")
        print("==================================================")
        sys.exit(0)
    else:
        print("Service Layer: Unreachable or authentication failed")
        print(f"Login: failed - {message}")
        print("Status: DISCONNECTED")
        print("==================================================")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
