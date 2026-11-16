import asyncio
import re
from app.sap.client import sap_client
from app.services.agent_service import agent_service

async def main():
    message = "What is the address of customer C20000?"
    entity = agent_service.detect_entity(message)
    code_match = re.search(r"\b([CVL]\d{3,6}|ITM-?\d+|WH-?[A-Za-z0-9]+|\d{1,4})\b", message, re.IGNORECASE)
    key = code_match.group(1).upper() if code_match else None
    print(f"DEBUG: entity={entity}, key={key}")
    
    rec_get = await sap_client.get(entity, key=key)
    print(f"DEBUG: sap_client.get returned: {bool(rec_get)}, type={type(rec_get)}, keys={list(rec_get.keys()) if isinstance(rec_get, dict) else None}")

if __name__ == "__main__":
    asyncio.run(main())
