import sys
sys.path.insert(0, 'backend')
import re
# pyrefly: ignore [missing-import]
from app.services.agent_service import AgentService

m = "give the business partner whose address is delhi"
print("DETECTED ENTITY:", AgentService.detect_entity(m))
res = AgentService.parse_query_filters('BusinessPartners', m)
print("PARSED FILTERS:", res)

# Check search_term line by line
code_match = re.search(r"\b([CVL]\d{3,6}|ITM-?\d+|WH-?[A-Za-z0-9]+)\b", m, re.IGNORECASE)
print("CODE MATCH:", code_match)
search_match = re.search(
    r"(?:search|find|for|matching|named?)\s+(?:customer|item|warehouse|partner)?\s*['\"]?([A-Za-z0-9_-]{2,25})['\"]?",
    m,
    re.IGNORECASE
)
print("SEARCH MATCH:", search_match)
if search_match:
    print("SEARCH MATCH 0:", repr(search_match.group(0)))
    print("SEARCH MATCH 1:", repr(search_match.group(1)))
