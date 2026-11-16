"""
Intent and Entity Router for Autonomous SAP AI Agent.
Categorizes natural language input into structured intents and extracts OData filter parameters.
"""
import re
from typing import Any, Dict, List, Optional
from app.agent.schemas import AgentIntent, SAPEntity


def detect_intent(message: str) -> str:
    """Detect intent: CONFIRM_CREATE, CREATE, UPDATE, SPECIFIC_QUERY, QUERY, HEALTH, or EXPLAIN."""
    m = message.strip().lower()

    # Health Check
    if any(h in m for h in ["sap health", "check health", "ping sap", "test connection", "connection status", "is sap up", "check sap health"]):
        return AgentIntent.HEALTH.value

    # Master Data Creation takes precedence over generic confirmation
    create_keywords = [
        "create", "add new", "register new", "register warehouse", "register item", "register partner",
        "insert", "new customer", "new vendor", "new business partner", "new item", "new warehouse",
        "make a customer", "make a business partner", "make an item", "make a warehouse", "create partner",
        "create bp", "create businesspartner", "add item", "add warehouse", "new bp", "register",
        "create item master", "create an item master", "add item master", "new item master",
        "create warehouse master", "create a warehouse", "create a business partner", "create a customer",
        "create a vendor", "create an item"
    ]
    if any(re.search(rf"\b{kw}\b", m) for kw in create_keywords):
        return "CREATE"

    # Direct confirmation triggers (must strictly be confirmation phrase and not entity creation)
    confirm_exact = [
        "confirm", "post to sap", "post it", "proceed", "create it",
        "submit", "confirm creation", "yes please", "post now", "send to sap",
        "create now", "save to sap", "confirm and post", "confirm & create in sap",
        "yes please create it", "please create it", "post", "save it", "save", "yes"
    ]
    has_entity_word = any(re.search(rf"\b{kw}\b", m) for kw in ["item", "items", "customer", "customers", "vendor", "vendors", "supplier", "suppliers", "partner", "partners", "warehouse", "warehouses", "master", "bp", "cardcode", "itemcode", "warehousecode"])
    if not has_entity_word and any(re.match(rf"^{re.escape(ck)}(?:\s+|$|[!.]*)", m) for ck in confirm_exact):
        return AgentIntent.CONFIRM_CREATE.value

    # Update Master Data (e.g. "change phone to 9876543210", "update item ITM-001 name to...", "update warehouse 01 city to...")
    update_verbs = ["change", "update", "set", "modify", "edit", "replace", "switch", "alter", "assign"]
    if any(re.search(rf"\b{verb}\b", m) for verb in update_verbs):
        return AgentIntent.UPDATE.value

    # Specific Attribute Query (e.g. "what is the address of customer C20000", "phone number of V10000", "tax rate of ITM-001", "where is warehouse WH01 located?")
    has_specific_code = bool(re.search(r"\b([CVL]\d{3,6}|ITM-?[A-Za-z0-9_-]+|WH-[A-Za-z0-9_-]+|WH\d{1,4})\b", message))
    attr_patterns = [
        r"\b(?:what|where|who|how)\s+(?:is|are)\s+(?:the\s+)?(address|phone|mobile|telephone|email|tax|taxrate|gst|gstin|pan|price|group|uom|unit|location|city|rate|status|terms|currency|material|hsn|details|overview|stock|quantity|inventory|name|barcode)\b",
        r"\b(?:address|phone|mobile|telephone|email|tax|taxrate|gst|gstin|pan|price|group|uom|unit|location|city|rate|status|terms|currency|material|hsn|details|overview|stock|quantity|inventory|name|barcode)\s+(?:of|for)\s+",
        r"\b(?:details|tell me about|info|show|view)\s+(?:of|about|for)\s*(?:customer|vendor|supplier|partner|item|product|warehouse)\s*['\"]?([A-Za-z0-9_-]+)['\"]?",
        r"\bwhere\s+is\s+(?:the\s+)?(?:warehouse|customer|vendor|supplier|partner|item)?\s*['\"]?([A-Za-z0-9_-]+)['\"]?\s*(?:located|situated|based)?\b",
    ]
    if any(re.search(pat, m) for pat in attr_patterns) and (has_specific_code or " of " in m or " for " in m or "located" in m):
        return AgentIntent.SPECIFIC_QUERY.value

    # Conditional Queries / Filter clauses take precedence as QUERY intent
    has_condition_pattern = any([
        re.search(r"\b(whose|which\s+have|which\s+has|having|with|without|not\s+available|unavailable|missing|unregistered|drafts\s+not\s+synced|not\s+in\s+realtime|not\s+in\s+real-time|not\s+synced|located\s+in)\b", m),
        re.search(r"(?:\w+\s+where\b|\bwhere\s+(?:the\s+)?(?:city|state|country|balance|price|stock|quantity|status|hsn|tax|gst|pan|phone|name|rate|is\s+greater|is\s+less)\b)", m),
        re.search(r"\b(greater\s+than|greter\s+than|more\s+than|higher\s+than|above|exceeding|less\s+than|lower\s+than|below|under|at\s+least|at\s+most)\b", m),
        re.search(r"(?:[><]=?|!=|=)\s*[\d.]+", m),
        re.search(r"\b(balance|price|stock|quantity|hsn|gst|phone|email)\s+(?:greater|greter|less|more|above|below|missing|not\s+available|without|>|<|>=|<=)", m),
        re.search(r"\b(customers?|vendors?|suppliers?|partners?|warehouses?|items?|products?)\s+(?:in|from|at)\s+[a-zA-Z]+", m),
        re.search(r"\b(?:vendor|customer|supplier|partner|item|product|warehouse)\s+balance\b", m),
        re.search(r"\b(?:bp|item|warehouse)\s+master\b", m),
        re.search(r"\b(unregistered|simulated)\s+(?:business\s*partners?|customers?|vendors?|suppliers?|bps?)\b", m)
    ])
    if has_condition_pattern:
        return AgentIntent.QUERY.value

    # General Table Query / List / Audit
    query_verbs = [
        "give", "show", "list", "get", "fetch", "search", "find", "top", "display",
        "retrieve", "how many", "all", "identify", "detect", "audit", "check", "report", "view"
    ]
    if any(re.search(rf"\b{verb}\b", m) for verb in query_verbs):
        return AgentIntent.QUERY.value

    plural_entities = ["items", "customers", "vendors", "suppliers", "partners", "warehouses", "business partners", "item masters", "warehouse masters", "customer masters"]
    if any(re.search(rf"\b{re.escape(pe)}\b", m) for pe in plural_entities):
        return AgentIntent.QUERY.value

    return AgentIntent.EXPLAIN.value


def detect_entity(message: str) -> str:
    """Detect allowlisted SAP entity: BusinessPartners, Items, or Warehouses."""
    m = message.lower()
    # 1. Specialized combinations (e.g. items across warehouses, customers and vendors)
    if re.search(r"\bitems?\b", m) and re.search(r"\b(?:stock|quantity|inventory)\b", m) and re.search(r"\bwarehouses?\b", m):
        return SAPEntity.ITEMS.value
    if re.search(r"\b(?:customers?|vendors?|suppliers?|partners?|business\s*partners?)\b", m):
        return SAPEntity.BUSINESS_PARTNERS.value
    if re.search(r"\b(item\s*masters?|items?|products?|skus?|oitm|materials?|goods)\b", m):
        return SAPEntity.ITEMS.value
    if re.search(r"\b(warehouse\w*|owhs|storage|depots?|binactivat|whs\w*|warehousecode|warehousename)\b", m):
        return SAPEntity.WAREHOUSES.value

    # 2. Standard code prefixes
    if re.search(r"\b[CVL]\d{3,6}\b", message, re.IGNORECASE):
        return SAPEntity.BUSINESS_PARTNERS.value
    if re.search(r"\b(ITM-?[A-Za-z0-9]+|I\d{3,6})\b", message, re.IGNORECASE):
        return SAPEntity.ITEMS.value
    if re.search(r"\b(WH-\d+|WH-[A-Za-z0-9_-]+|WH\d{1,4})\b", message, re.IGNORECASE):
        return SAPEntity.WAREHOUSES.value

    # 3. Secondary attribute keywords fallback
    if re.search(r"\b(gstno|gstin|panno|paymentterms|federaltaxid|controlaccount|cardcode|cardname|cardtype|balance|account\s+balance)\b", m):
        return SAPEntity.BUSINESS_PARTNERS.value
    if re.search(r"\b(inventoryuom|itemsgroupcode|taxrate|salesunit|purchaseunit|barcode|hsn|sac|itemname|itemcode|materialtype|taxcategory|itemmanagementmethod|stock|quantity|price)\b", m):
        return SAPEntity.ITEMS.value

    return SAPEntity.BUSINESS_PARTNERS.value


def parse_query_filters(entity: str, message: str) -> Dict[str, Any]:
    """
    Parses complex natural language query into structured filter definitions and OData $filter clause.
    """
    m = message.strip()
    m_lower = m.lower()

    subtype: Optional[str] = None
    entity_label = "Business Partners" if entity == "BusinessPartners" else ("Items" if entity == "Items" else "Warehouses")
    locations: List[str] = []
    numeric_filters: List[Dict[str, Any]] = []
    missing_fields: List[str] = []
    not_in_realtime: bool = False
    unregistered: bool = False
    logical_operator: str = "AND"
    filter_descriptions: List[str] = []

    # Check for logical operator (OR vs AND)
    if re.search(r"\b(?:or|either)\b", m_lower):
        logical_operator = "OR"

    # 1. Subtype Detection
    if entity == "BusinessPartners":
        if re.search(r"\b(customer|customers|client|clients)\b", m_lower) and not re.search(r"\b(supplier|suppliers|vendor|vendors)\b", m_lower):
            subtype = "cCustomer"
            entity_label = "Customer Business Partners"
        elif re.search(r"\b(supplier|suppliers|vendor|vendors)\b", m_lower):
            subtype = "cSupplier"
            entity_label = "Supplier Business Partners"
        elif re.search(r"\b(lead|leads)\b", m_lower):
            subtype = "cLid"
            entity_label = "Lead Business Partners"

    elif entity == "Warehouses":
        if re.search(r"\b(inactive|disabled|closed)\b", m_lower):
            subtype = "tYES"
            entity_label = "Inactive Warehouses"
        elif re.search(r"\b(active|enabled|open)\b", m_lower):
            subtype = "tNO"
            entity_label = "Active Warehouses"

    # 2. Location / Address Extraction
    loc_patterns = [
        r"\b(?:whose\s+)?(?:address|location|city)\s+(?:is|=|in|contains|as|at)?\s*['\"]?([a-zA-Z\s]+?)['\"]?(?:\s+(?:and|or|with|where|whose|having|with\s+balance|balance|greter|greater|less|price|stock|not|missing)|$|[?!.])",
        r"\b(?:located\s+in|location\s+is|city\s+is|in\s+city)\s+['\"]?([a-zA-Z\s]+?)['\"]?(?:\s+(?:and|or|with|where|whose|having|with\s+balance|balance|greter|greater|less|price|stock|not|missing)|$|[?!.])",
        r"\b(?:warehouses?|depots?|customers?|vendors?|suppliers?|partners?|business\s*partners?|bps?)\s+in\s+['\"]?([a-zA-Z\s]+?)['\"]?(?:\s+(?:and|or|with|where|whose|having|with\s+balance|balance|greter|greater|less|price|stock|not|missing)|$|[?!.])"
    ]

    extracted_locs = []
    for pat in loc_patterns:
        matches = re.finditer(pat, m_lower)
        for match in matches:
            cand = match.group(1).strip()
            cand = re.sub(r"^(?:the|a|an)\s+", "", cand).strip()
            cand = re.sub(r"\s+(?:master|data|records?|business|partners?|customers?|vendors?|items?|warehouses?)$", "", cand).strip()
            if cand and cand not in ["master", "data", "partner", "business", "customer", "vendor", "item", "warehouse", "all", "the", "realtime", "sap"]:
                extracted_locs.append(cand)

    # Common city lookup fallback
    known_cities = ["delhi", "mumbai", "bangalore", "bengaluru", "pune", "ahmedabad", "chennai", "kolkata", "gurgaon", "gurugram", "hyderabad", "faridabad", "navi mumbai", "noida", "jaipur"]
    for city in known_cities:
        if re.search(rf"\b{city}\b", m_lower) and city not in [loc.lower() for loc in extracted_locs]:
            extracted_locs.append(city)

    for loc in extracted_locs:
        clean_loc = loc.title() if len(loc) > 3 else loc.upper()
        if clean_loc not in locations:
            locations.append(clean_loc)
            filter_descriptions.append(f"located in '{clean_loc}'")

    # 3. Numeric Filters (Balance, Price, Stock) with typo tolerance
    def parse_op(raw_op: str) -> str:
        op_str = raw_op.strip().lower()
        if any(k in op_str for k in ["greater than or equal", "greter than or equal", "more than or equal", "at least", ">="]):
            return "ge"
        if any(k in op_str for k in ["greater", "greter", "more than", "higher", "above", "exceeding", "over", ">", "gt"]):
            return "gt"
        if any(k in op_str for k in ["less than or equal", "lower than or equal", "at most", "<="]):
            return "le"
        if any(k in op_str for k in ["less", "lower", "below", "under", "smaller", "<", "lt"]):
            return "lt"
        if any(k in op_str for k in ["equal", "equals", "is", "=", "=="]):
            return "eq"
        if any(k in op_str for k in ["not equal", "!=", "ne"]):
            return "ne"
        return "gt"

    num_patterns = [
        r"\b(account\s+balance|current\s+balance|vendor\s+balance|customer\s+balance|balance|price|unit\s+price|stock|inventory|quantity|quantity\s+on\s+stock)\s+(?:is\s+)?(greater\s+than\s+or\s+equal\s+to|greter\s+than\s+or\s+equal\s+to|more\s+than\s+or\s+equal\s+to|greater\s+than|greter\s+than|more\s+than|higher\s+than|exceeding|above|over|less\s+than\s+or\s+equal\s+to|less\s+than|lower\s+than|below|under|at\s+least|at\s+most|equal\s+to|equals|is|=|>=|<=|>|<|!=)\s+([\d,]+(?:\.\d+)?)\b",
        r"\b(balance|price|stock|quantity)\s*([><]=?|!=|=)\s*([\d,]+(?:\.\d+)?)\b",
        r"\bwhere\s+(?:account\s+)?(balance|price|stock|quantity)\s+(?:is\s+)?(greater\s+than|greter\s+than|more\s+than|less\s+than|lower\s+than|above|below|over|under|[><]=?)\s+([\d,]+(?:\.\d+)?)\b",
        r"\bwith\s+(?:account\s+)?(balance|price|stock|quantity)\s+(?:is\s+)?(greater\s+than|greter\s+than|more\s+than|less\s+than|lower\s+than|above|below|over|under|[><]=?)\s+([\d,]+(?:\.\d+)?)\b",
        r"\b(stock|price)\s+(greater\s+than|greter\s+than|more\s+than|less\s+than|above|below|[><]=?)\s+([\d,]+(?:\.\d+)?)\b"
    ]

    seen_numeric_fields = set()
    for pat in num_patterns:
        matches = re.finditer(pat, m_lower)
        for match in matches:
            raw_f, raw_op, raw_val = match.groups()
            val = float(raw_val.replace(",", ""))
            op = parse_op(raw_op)

            field_name = "CurrentAccountBalance"
            alt_field = "Balance"
            if "price" in raw_f:
                field_name = "Price"
                alt_field = None
            elif "stock" in raw_f or "quantity" in raw_f or "inventory" in raw_f:
                field_name = "QuantityOnStock"
                alt_field = None

            if field_name not in seen_numeric_fields:
                seen_numeric_fields.add(field_name)
                numeric_filters.append({
                    "field": field_name,
                    "alt_field": alt_field,
                    "operator": op,
                    "value": val
                })
                op_sym = ">" if op == "gt" else (">=" if op == "ge" else ("<" if op == "lt" else ("<=" if op == "le" else "=")))
                filter_descriptions.append(f"{field_name} {op_sym} {val}")

    # 4. Missing / Unavailable Field Audits
    hsn_patterns = [
        r"\b(?:whose|those|which|where|with|having|for\s+which)?\s*hsn(?:\s+code)?(?:\s+is|\s+are)?\s+(?:not\s+available|unavailable|missing|empty|null|none|blank|zero|0)\b",
        r"\b(?:without|missing|no|not\s+having)\s+hsn(?:\s+code)?\b",
        r"\bhsn(?:\s+code)?\s+(?:is\s+|are\s+)?not\s+available\b",
        r"\bhsn(?:\s+code)?\s+unavailable\b"
    ]
    if any(re.search(p, m_lower) for p in hsn_patterns):
        if "HSN" not in missing_fields:
            missing_fields.append("HSN")
            filter_descriptions.append("HSN not available")

    gst_patterns = [
        r"\b(?:whose|those|which|where|with|having|for\s+which)?\s*(?:gst|gstin|tax\s+id|federaltaxid)(?:\s+number|\s+no)?(?:\s+is|\s+are)?\s+(?:not\s+available|unavailable|missing|empty|null|none|blank|unregistered)\b",
        r"\b(?:without|missing|no|not\s+having)\s+(?:gst|gstin|tax\s+id)(?:\s+number|\s+no)?\b",
        r"\b(?:gst|gstin)\s+(?:is\s+|are\s+)?not\s+available\b",
        r"\b(?:gst|gstin)\s+unavailable\b",
        r"\bunregistered\b"
    ]
    if any(re.search(p, m_lower) for p in gst_patterns):
        if "GST" not in missing_fields:
            missing_fields.append("GST")
            filter_descriptions.append("GST not available")

    has_missing_phone = bool(re.search(r"\b(?:missing|without|no|not\s+available)\s+phone\b|\bphone\s+not\s+available\b", m_lower))
    has_missing_email = bool(re.search(r"\b(?:missing|without|no|not\s+available)\s+email\b|\bemail\s+not\s+available\b", m_lower))
    if re.search(r"\bmissing\s+phone\s+or\s+email\b|\bwithout\s+phone\s+or\s+email\b", m_lower):
        has_missing_phone = True
        has_missing_email = True

    if has_missing_phone and "Phone" not in missing_fields:
        missing_fields.append("Phone")
        filter_descriptions.append("Phone missing")
    if has_missing_email and "Email" not in missing_fields:
        missing_fields.append("Email")
        filter_descriptions.append("Email missing")

    # 5. Real-time / Sync Status & Registration Audits
    if any(re.search(p, m_lower) for p in [
        r"\bnot\s+in\s+realtime(?:\s+sap)?\b",
        r"\bnot\s+in\s+real-time(?:\s+sap)?\b",
        r"\bnot\s+synced(?:\s+to\s+sap)?\b",
        r"\bdrafts?\s+not\s+synced(?:\s+to\s+sap)?\b",
        r"\bsimulated\s+records?\b"
    ]):
        not_in_realtime = True
        filter_descriptions.append("not synced to realtime SAP")

    if any(re.search(p, m_lower) for p in [
        r"\bunregistered\s+(?:business\s*partners?|customers?|vendors?|suppliers?|bps?|parties|party)\b",
        r"\bunregistered\s+bp\b",
        r"\bunregistered\b"
    ]):
        unregistered = True
        if "GST" not in missing_fields and entity == "BusinessPartners":
            missing_fields.append("GST")
        filter_descriptions.append("unregistered status")

    # 6. Build OData $filter clause
    subtype_clause: Optional[str] = None
    if subtype:
        if subtype in ["cCustomer", "cSupplier", "cLid"]:
            subtype_clause = f"CardType eq '{subtype}'"
        elif subtype in ["tYES", "tNO"]:
            subtype_clause = f"Inactive eq '{subtype}'"

    cond_parts: List[str] = []

    if locations:
        if entity == "BusinessPartners":
            loc_or = " or ".join([f"(contains(City, '{loc}') or contains(Address, '{loc}'))" for loc in locations])
        elif entity == "Warehouses":
            loc_or = " or ".join([f"(contains(City, '{loc}') or contains(Street, '{loc}'))" for loc in locations])
        else:
            loc_or = " or ".join([f"contains(ItemName, '{loc}')" for loc in locations])
        cond_parts.append(f"({loc_or})" if len(locations) > 1 else loc_or)

    if numeric_filters:
        for nf in numeric_filters:
            f_name = nf["field"]
            op = nf["operator"]
            val = nf["value"]
            if nf.get("alt_field") and entity == "BusinessPartners":
                cond_parts.append(f"({f_name} {op} {val} or {nf['alt_field']} {op} {val})")
            else:
                cond_parts.append(f"{f_name} {op} {val}")

    if missing_fields:
        if "HSN" in missing_fields:
            if entity == "BusinessPartners":
                cond_parts.append("(FederalTaxID eq null or FederalTaxID eq '' or FederalTaxID eq 'UNREGISTERED' or FederalTaxID eq 'URP' or FederalTaxID eq 'N/A')")
            else:
                cond_parts.append("(ChapterID eq null or ChapterID eq 0)")
        if "GST" in missing_fields:
            cond_parts.append("(FederalTaxID eq null or FederalTaxID eq '' or FederalTaxID eq 'UNREGISTERED' or FederalTaxID eq 'URP' or FederalTaxID eq 'N/A')")
        if "Phone" in missing_fields and "Email" in missing_fields:
            cond_parts.append("(Phone1 eq null or EmailAddress eq null)")
        elif "Phone" in missing_fields:
            cond_parts.append("(Phone1 eq null or Phone1 eq '')")
        elif "Email" in missing_fields:
            cond_parts.append("(EmailAddress eq null or EmailAddress eq '')")

    if not_in_realtime:
        cond_parts.append("_simulated eq true")

    combined_conditions: Optional[str] = None
    if cond_parts:
        joiner = " or " if logical_operator == "OR" else " and "
        if len(cond_parts) > 1:
            combined_conditions = f"({joiner.join(cond_parts)})"
        else:
            combined_conditions = cond_parts[0]

    odata_filter: Optional[str] = None
    if subtype_clause and combined_conditions:
        odata_filter = f"{subtype_clause} and {combined_conditions}"
    elif subtype_clause:
        odata_filter = subtype_clause
    elif combined_conditions:
        odata_filter = combined_conditions

    # 7. Cleaned search term extraction
    search_term: Optional[str] = None
    stopwords = {
        "customer", "customers", "vendor", "vendors", "supplier", "suppliers", "partner", "partners",
        "business", "item", "items", "warehouse", "warehouses", "top", "the", "first", "all",
        "whose", "where", "which", "having", "with", "without", "for", "from", "in", "is", "are",
        "delhi", "mumbai", "pune", "bangalore", "greater", "greter", "less", "than", "balance",
        "price", "stock", "hsn", "gst", "phone", "email", "realtime", "sap", "unregistered",
        "what", "when", "while", "why", "who", "whom", "give", "show", "list", "find", "search"
    }
    code_match = re.search(r"\b([CVL]\d{3,6}|ITM-?\d+|WH-\d+|WH-[A-Za-z0-9_-]+|WH\d{1,4})\b", m, re.IGNORECASE)
    if code_match and code_match.group(1).lower() not in stopwords:
        search_term = code_match.group(1).strip()
    else:
        search_match = re.search(
            r"(?:search|find|for|matching|named?)\s+(?:customer|item|warehouse|partner)?\s*['\"]?([A-Za-z0-9_-]{2,25})['\"]?",
            m,
            re.IGNORECASE
        )
        if search_match:
            cand = search_match.group(1).strip()
            if cand.lower() not in stopwords:
                search_term = cand

    filter_summary = ", ".join(filter_descriptions) if filter_descriptions else ""

    return {
        "entity": entity,
        "subtype": subtype,
        "entity_label": entity_label,
        "locations": locations,
        "numeric_filters": numeric_filters,
        "missing_fields": missing_fields,
        "not_in_realtime": not_in_realtime,
        "unregistered": unregistered,
        "logical_operator": logical_operator,
        "odata_filter": odata_filter,
        "search_term": search_term,
        "filter_summary": filter_summary
    }
