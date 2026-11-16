import sys
sys.path.insert(0, 'backend')
import re
# pyrefly: ignore [missing-import]
from app.services.agent_service import AgentService

message = "change the customer name which have cardcode C20000 to Cinntra Tech Global"
entity = "BusinessPartners"
key = "C20000"

text_for_fields = message
text_for_fields = re.sub(r"\bwhich\s+(?:have|has)\s+(?:cardcode|itemcode|code|warehousecode)\s*['\"]?" + re.escape(str(key)) + r"['\"]?", "", text_for_fields, flags=re.IGNORECASE)
text_for_fields = re.sub(r"\b(?:with|having)\s+(?:cardcode|itemcode|code|warehousecode)\s*['\"]?" + re.escape(str(key)) + r"['\"]?", "", text_for_fields, flags=re.IGNORECASE)
text_for_fields = re.sub(r"\bwhich\s+(?:have|has)\s+(?:cardcode|itemcode|code|warehousecode)\b", "", text_for_fields, flags=re.IGNORECASE)
text_for_fields = re.sub(r"(?:for|on|of|in)\s+(?:customer|vendor|item|warehouse|partner)?\s*['\"]?" + re.escape(str(key)) + r"['\"]?", "", text_for_fields, flags=re.IGNORECASE)
text_for_fields = re.sub(r"(?:customer|vendor|item|warehouse|partner)\s+['\"]?" + re.escape(str(key)) + r"['\"]?", "", text_for_fields, flags=re.IGNORECASE)
text_for_fields = re.sub(r"\b" + re.escape(str(key)) + r"\b", "", text_for_fields, flags=re.IGNORECASE)

print("AFTER KEY STRIP:", repr(text_for_fields))

text_for_fields = re.sub(r"^(?:please\s+)?(?:change|update|set|modify)\s+(?:the\s+)?", "", text_for_fields, flags=re.IGNORECASE)
print("AFTER CHANGE STRIP:", repr(text_for_fields))
text_for_fields = re.sub(r"\b(?:of|for)\s+(?:customer|vendor|item|warehouse|partner)?\b", "", text_for_fields, flags=re.IGNORECASE).strip()
print("AFTER OF/FOR STRIP:", repr(text_for_fields))

segments = re.split(r"\s+and\s+|,\s*", text_for_fields)
print("SEGMENTS:", segments)
for seg in segments:
    seg = seg.strip()
    field_match = re.search(r"^(?:the\s+)?([a-zA-Z0-9\s_]+?)\s*(?:to|as|is|=|:)\s*(.+)$", seg, re.IGNORECASE)
    print("FIELD MATCH:", field_match)
    if field_match:
        raw_f, raw_v = field_match.groups()
        print("RAW_F:", repr(raw_f), "RAW_V:", repr(raw_v))
        norm_field = AgentService.normalize_field_name(entity, raw_f)
        print("NORM FIELD:", norm_field)
