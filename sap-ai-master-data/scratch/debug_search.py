import sys
sys.path.insert(0, 'backend')
# pyrefly: ignore [missing-import]
from app.services.agent_service import AgentService

prompts = [
    "give the business partner whose address is delhi",
    "list customers located in mumbai",
    "warehouses in delhi",
    "list all Customer where account balance greater than 1000",
    "vendor balance greter than 1000",
    "customers with balance less than 500",
    "items with price greater than 500",
    "stock greater than 100",
    "list all item master data whose HSN not available",
    "items without HSN code",
    "bp master whose GST Not available",
    "bp master whose GST Not available or not in realtime SAP",
    "unregistered business partners",
    "drafts not synced to SAP"
]

for p in prompts:
    ent = AgentService.detect_entity(p)
    res = AgentService.parse_query_filters(ent, p)
    print(f"\nPROMPT: {p}")
    print(f"ENTITY: {ent}")
    print(f"FILTERS: {res}")
