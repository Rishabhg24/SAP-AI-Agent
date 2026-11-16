"""
Multi-turn Slot Filling and Master Data Creation Session Manager.
Tracks creation drafts, collects missing mandatory fields, and applies smart defaults.
"""
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from app.agent.field_mappings import (
    MANDATORY_CREATION_SCHEMA,
    normalize_field_name,
    validate_field_value,
)
from app.agent.intent_router import detect_entity
from app.services.chat_service import nvidia_chat_service
from app.utils.logging import logger


def parse_creation_fields(message: str, entity: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    Extract field-value pairs for master data creation from natural language.
    Handles multi-segment phrases and natural prompt styles.
    """
    fields: Dict[str, Any] = {}
    errors: List[str] = []
    text = message.strip()

    # 1. High-level entity-specific natural language pattern extraction
    if entity == "BusinessPartners":
        # Direct inverted code pattern: "<val> is [the] [card]code", "<val> as [the] [card]code", "use <val> as code"
        inv_code_m = re.search(
            r"\b([A-Za-z0-9_-]{2,15})\s+(?:is|as)\s+(?:the\s+)?(?:customer|vendor|supplier|bp|partner|card)?\s*code\b",
            text,
            re.IGNORECASE
        )
        if inv_code_m and inv_code_m.group(1).upper() not in ["IS", "AS", "THE", "A", "AN", "NEW", "ITEM", "CODE", "THIS"]:
            fields["CardCode"] = inv_code_m.group(1).upper()

        # Direct CardCode Regex (extract first so code phrases aren't eaten by name)
        if "CardCode" not in fields:
            code_m = re.search(
                r"\b(?:(?:customer|vendor|supplier|bp|partner|card)?\s*code|cardcode)\s*[:=]?\s*['\"]?([CVL]?[A-Za-z0-9_-]{2,15})['\"]?\b",
                text,
                re.IGNORECASE
            )
            if code_m and code_m.group(1).upper() not in ["IS", "AS", "THE", "A", "AN", "NEW", "ITEM", "CODE", "THIS"]:
                fields["CardCode"] = code_m.group(1).upper()

        # Direct code formats (e.g. CV02, CV24, C20099, V10099, BP01, C01, V01, etc.)
        if "CardCode" not in fields:
            m_direct_c = re.search(r"\b((?:CV|BP|C|V|L)\d{1,8})\b", text, re.IGNORECASE)
            if m_direct_c and m_direct_c.group(1).upper() not in ["IS", "AS", "THE", "A", "AN", "NEW", "CODE"]:
                fields["CardCode"] = m_direct_c.group(1).upper()

        # Extract CardType
        is_vendor = bool(re.search(r"\b(vendor|supplier)\b", text, re.IGNORECASE))
        is_customer = bool(re.search(r"\b(customer|client)\b", text, re.IGNORECASE))
        is_lead = bool(re.search(r"\b(lead)\b", text, re.IGNORECASE))
        if is_vendor and not is_customer:
            fields["CardType"] = "cSupplier"
        elif is_customer and not is_vendor:
            fields["CardType"] = "cCustomer"
        elif is_vendor and is_customer:
            if fields.get("CardCode", "").startswith("V"):
                fields["CardType"] = "cSupplier"
            elif fields.get("CardCode", "").startswith("C"):
                fields["CardType"] = "cCustomer"
            else:
                v_pos = text.lower().find("vendor")
                c_pos = text.lower().find("customer")
                fields["CardType"] = "cSupplier" if (v_pos != -1 and (c_pos == -1 or v_pos < c_pos)) else "cCustomer"
        elif is_lead:
            fields["CardType"] = "cLid"

        # Check inverted name pattern: "<val> is [business] partner", "<val> [business] partner", "<val> [is] company"
        # Only check when text does not start with an action command (like "create business partner ...")
        if not re.match(r"^(?:create|add|new|register|make|insert)\b", text, re.IGNORECASE):
            inv_name_m = re.search(
                r"(?:^|\band\s+|\,\s*)\s*([A-Za-z0-9&.,_-]{2,50}?)\s+(?:is\s+)?(?:the\s+)?(?:business\s*partner|partner|company)\b",
                text,
                re.IGNORECASE
            )
            if inv_name_m:
                cand_inv = inv_name_m.group(1).strip()
                cand_inv = re.sub(r"^(?:and|is|a|an|the|new|create|add|register|for)\s+", "", cand_inv, flags=re.IGNORECASE).strip()
                if cand_inv.lower() not in ["a", "the", "business partner", "partner", "customer", "vendor", "supplier", "new", "code", "item", "this", "create", "add", "register"] and not cand_inv.lower().startswith("code "):
                    fields["CardName"] = cand_inv

        # Extract Name if "called X", "named X", "name is X", "company X", or "partner X"
        if "CardName" not in fields:
            name_m = re.search(
                r"\b(?:called|named|(?:company|partner|customer|vendor|supplier)?\s*name|company|partner|business\s*partner)\s*(?:is|:|=)?\s*['\"]?([A-Za-z0-9\s&.,_-]{2,50}?)['\"]?(?=\s+(?:with|in|at|having|gst|pincode|address|cardcode|phone|\,|$|\sand\b))",
                text,
                re.IGNORECASE
            )
            if name_m:
                cand_name = name_m.group(1).strip()
                cand_name = re.sub(r"^(?:called|named|is|a|an|the|customer|vendor|supplier|business\s*partner|code)\s+", "", cand_name, flags=re.IGNORECASE).strip()
                if cand_name.lower() not in ["a", "the", "business partner", "customer", "vendor", "supplier", "new", "code"] and not cand_name.lower().startswith("code "):
                    fields["CardName"] = cand_name

        if not fields.get("CardName"):
            direct_cand = re.search(
                r"\b(?:create|add|register|insert|new)\s+(?:a\s+|an\s+)?(?:vendor|customer|supplier|partner|business\s*partner|bp)\s+(?:called\s+|named\s+)?(?:name\s+|named\s+)?['\"]?([A-Za-z0-9&.,_-]+(?:\s+[A-Za-z0-9&.,_-]+){0,4}?)['\"]?(?=\s+(?:with|having|code|cardcode|phone|at|in|gst|pan|address|,|\sand\s|$|\b(?:mumbai|delhi|bangalore|chennai|pune|hyderabad|kolkata|ahmedabad)\b))",
                text,
                re.IGNORECASE
            )
            if direct_cand:
                cand_name = direct_cand.group(1).strip()
                cand_name = re.sub(r"^(?:called|named|is|a|an|the|customer|vendor|supplier|business\s*partner|code|name)\s+", "", cand_name, flags=re.IGNORECASE).strip()
                # If cand_name ends with a known city, strip the city
                cand_name = re.sub(r"\s+\b(?:mumbai|delhi|bangalore|chennai|pune|hyderabad|kolkata|ahmedabad)\b$", "", cand_name, flags=re.IGNORECASE).strip()
                if cand_name.lower() not in ["a", "the", "business partner", "customer", "vendor", "supplier", "new", "code", "item", "master", "name"] and not cand_name.lower().startswith("code "):
                    fields["CardName"] = cand_name

        if not fields.get("CardName"):
            name_simple = re.search(r"\b(?:name\s*(?:is|:|=)?\s*['\"]?([A-Za-z0-9\s&.,_-]{2,50}?)['\"]?)(?=\s+(?:with|in|at|having|gst|cardcode|phone|\,|$))", text, re.IGNORECASE)
            if name_simple:
                c = name_simple.group(1).strip()
                if c.lower() not in ["a", "the", "is", "code", "customer", "vendor", "supplier"]:
                    fields["CardName"] = c

        # Extract Phone (including "update the phone of xyz to xyzphoneno", "phone 9876543210")
        phone_m = re.search(
            r"\b(?:(?:and\s+)?(?:update|change|set)\s+(?:the\s+)?phone\s+(?:of\s+[A-Za-z0-9_-]+\s+)?to|phone\s+of\s+[A-Za-z0-9_-]+\s+to|phone\s*(?:is|:|=|to)?|mobile\s*(?:is|:|=|to)?|contact\s*(?:is|:|=|to)?|telephone\s*(?:is|:|=|to)?)\s*['\"]?(\+?[A-Za-z0-9\s-]{3,20})\b",
            text,
            re.IGNORECASE
        )
        if phone_m:
            raw_phone = phone_m.group(1).strip()
            fields["Phone1"] = raw_phone
        else:
            p10_m = re.search(r"\b([6-9]\d{9})\b", text)
            if p10_m and any(pkw in text.lower() for pkw in ["phone", "mobile", "contact", "call"]):
                fields["Phone1"] = p10_m.group(1)

        # Extract Location / Address if "in X", "at X", "address is X"
        addr_m = re.search(r"\b(?:in|at|address(?:\s+is)?)\s+['\"]?([A-Za-z0-9\s,.-]{2,60}?)['\"]?(?=\s+(?:with|gst|pan|phone|cardcode|\,|$))", text, re.IGNORECASE)
        if addr_m:
            cand_addr = addr_m.group(1).strip().strip(",;")
            if cand_addr.lower() not in ["customer", "business partner", "mumbai", "delhi", "bangalore", "chennai", "pune", "hyderabad", "kolkata"]:
                fields["Address"] = cand_addr
            elif cand_addr:
                fields["Address"] = cand_addr.title()
                fields["City"] = cand_addr.title()

        # Direct GST Regex
        gst_m = re.search(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text, re.IGNORECASE)
        if gst_m:
            fields["GSTNo"] = gst_m.group(1).upper()
        elif re.search(r"\b(unregistered|urp)\b", text, re.IGNORECASE):
            fields["GSTNo"] = "UNREGISTERED"

        # Direct PAN Regex
        pan_m = re.search(r"\b([A-Z]{5}\d{4}[A-Z]{1})\b", text, re.IGNORECASE)
        if pan_m and not gst_m:
            fields["PANNo"] = pan_m.group(1).upper()

    elif entity == "Items":
        # Extract Item Name: "called X", "named X", "Item X"
        name_m = re.search(r"\b(?:called|named|item|product|description)\s+['\"]?([A-Za-z0-9\s&.,_-]{2,50}?)['\"]?(?=\s+(?:with|code|uom|in|tax|group|\,|$))", text, re.IGNORECASE)
        if name_m:
            cand_name = name_m.group(1).strip()
            cand_name = re.sub(r"^(?:called|named|is|a|an|the|item|product)\s+", "", cand_name, flags=re.IGNORECASE).strip()
            if cand_name.lower() not in ["a", "the", "new", "item", "master", "product"]:
                fields["ItemName"] = cand_name
        else:
            item_tail_m = re.search(r"\b(?:item|product)\s+([A-Za-z0-9\s_-]{2,30})$", text, re.IGNORECASE)
            if item_tail_m:
                cand_name = item_tail_m.group(1).strip()
                cand_name = re.sub(r"^(?:new|master)\s+", "", cand_name, flags=re.IGNORECASE).strip()
                if cand_name.lower() not in ["master", "new"]:
                    fields["ItemName"] = cand_name

        # Direct ItemCode Regex
        code_m = re.search(r"\b(?:code|itemcode|sku)\s+([A-Za-z0-9_-]{2,20})\b", text, re.IGNORECASE)
        if code_m:
            fields["ItemCode"] = code_m.group(1).upper()
        else:
            m_direct_itm = re.search(r"\b(ITM-?[A-Za-z0-9]+)\b", text, re.IGNORECASE)
            if m_direct_itm and m_direct_itm.group(1).upper() not in ["ITEM", "ITEMS"]:
                fields["ItemCode"] = m_direct_itm.group(1).upper()

        # UOM
        uom_m = re.search(r"\b(?:uom|unit(?:\s+of\s+measure)?|in)\s+([A-Za-z]{2,8})\b", text, re.IGNORECASE)
        if uom_m and uom_m.group(1).upper() in ["PCS", "BOX", "KG", "MTR", "SET", "LTR", "UNIT", "NOS", "EA"]:
            fields["InventoryUOM"] = uom_m.group(1).upper()

        # Tax Rate
        tax_m = re.search(r"\b(?:tax|taxrate|gst)\s*(?:is|of|rate)?\s*(\d{1,2})%?", text, re.IGNORECASE)
        if tax_m:
            fields["TaxRate"] = f"{tax_m.group(1)}%"

    elif entity == "Warehouses":
        # Extract Warehouse Name: "called X", "named X", "warehouse X"
        name_m = re.search(r"\b(?:called|named|warehouse|depot|name)\s+['\"]?([A-Za-z0-9\s&.,_-]{2,50}?)['\"]?(?=\s+(?:with|code|in|at|location|\,|$))", text, re.IGNORECASE)
        if name_m:
            cand_name = name_m.group(1).strip()
            cand_name = re.sub(r"^(?:called|named|is|a|an|the|warehouse|depot)\s+", "", cand_name, flags=re.IGNORECASE).strip()
            if cand_name.lower() not in ["a", "the", "new", "warehouse", "depot"]:
                fields["WarehouseName"] = cand_name

        # Direct Warehouse Code Regex
        code_m = re.search(r"\b(?:code|warehousecode|warehouse)\s+([A-Za-z0-9_-]{2,8})\b", text, re.IGNORECASE)
        if code_m and code_m.group(1).upper() not in ["NEW", "ADD", "CREATE", "THE"]:
            fields["WarehouseCode"] = code_m.group(1).upper()
        else:
            m_direct_wh = re.search(r"\b(WH-?[A-Za-z0-9]{1,6}|\d{1,4})\b", text, re.IGNORECASE)
            if m_direct_wh and m_direct_wh.group(1).upper() not in ["NEW", "ADD", "CREATE", "THE"]:
                fields["WarehouseCode"] = m_direct_wh.group(1).upper()

    # 2. Key-Value and Segment Pattern Matching
    segments = re.split(r"\s+and\s+|,\s*|;\s*|\n+", text)
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        clean_seg = re.sub(
            r"^(?:please\s+)?(?:create|add|register|insert|new|make)\s+(?:a\s+|an\s+|new\s+)?(?:business\s*partner|partner|customer|vendor|supplier|item\s*master|item|product|warehouse\s*master|warehouse|depot)?\s*(?:with\s+)?",
            "",
            seg,
            flags=re.IGNORECASE
        ).strip()
        if not clean_seg:
            continue

        # Inverted segment patterns (e.g. "cv24 is code", "abc is partner", "abc business partner")
        if entity == "BusinessPartners":
            inv_code = re.match(r"^([a-zA-Z0-9_-]{2,15})\s+(?:is|as)\s+(?:the\s+)?(?:customer|vendor|supplier|bp|partner|card)?\s*code$", clean_seg, re.IGNORECASE)
            if inv_code and inv_code.group(1).upper() not in ["IS", "AS", "THE", "A", "AN", "NEW", "CODE", "THIS"]:
                fields["CardCode"] = inv_code.group(1).upper()
                continue

            inv_name = re.match(r"^([a-zA-Z0-9\s&.,_-]{2,50}?)\s+(?:is\s+)?(?:the\s+)?(?:business\s*partner|partner|company\s*name|company)$", clean_seg, re.IGNORECASE)
            if inv_name:
                cand = inv_name.group(1).strip()
                cand = re.sub(r"^(?:and|is|a|an|the|new|create|add|for)\s+", "", cand, flags=re.IGNORECASE).strip()
                if cand.lower() not in ["a", "the", "business partner", "customer", "vendor", "supplier", "new", "code"]:
                    fields["CardName"] = cand
                    continue

        kv_m = re.search(r"^(?:the\s+|set\s+|change\s+|update\s+|with\s+)?([a-zA-Z0-9\s_]{2,25})\s*(?::|=|\bis\b|\bas\b|\bto\b)\s*(.+)$", clean_seg, re.IGNORECASE)
        if kv_m:
            raw_k, raw_v = kv_m.groups()
            norm_k = normalize_field_name(entity, raw_k)
            val = raw_v.strip().strip("'\"")
            if norm_k and val:
                is_v, n_val, err = validate_field_value(entity, norm_k, val)
                if is_v:
                    fields[norm_k] = n_val
                elif err:
                    errors.append(err)
        else:
            for field_kw in ["business partner", "businesspartner", "partner name", "partnername", "partner", "company name", "company", "cardname", "name", "customer name", "vendor name", "itemcode", "cardcode", "code", "warehousecode", "itemname", "warehousename", "taxrate", "inventoryuom", "uom", "itemsgroupcode", "group", "hsn", "location", "address", "city", "state", "gstno", "gst", "panno", "pan", "price"]:
                m_kw = re.search(rf"^(?:the\s+|with\s+)?({field_kw})\s+(.+)$", clean_seg, re.IGNORECASE)
                if m_kw:
                    raw_k, raw_v = m_kw.groups()
                    norm_k = normalize_field_name(entity, raw_k)
                    val = raw_v.strip().strip("'\"")
                    if norm_k and val:
                        is_v, n_val, err = validate_field_value(entity, norm_k, val)
                        if is_v:
                            fields[norm_k] = n_val
                        elif err:
                            errors.append(err)
                    break

    # If in BusinessPartners context and still missing CardCode or CardName, check paired tokens (e.g. "cv02 and abc", "cv24 and abc", "abc and cv24")
    if entity == "BusinessPartners" and ("CardCode" not in fields or "CardName" not in fields):
        non_empty = [s.strip() for s in segments if s.strip()]
        if len(non_empty) == 2:
            seg_a = re.sub(r"^(?:create|add|new|register)\s+(?:a\s+|an\s+)?(?:business\s*partner|partner|bp)?\s*", "", non_empty[0], flags=re.IGNORECASE).strip()
            seg_b = re.sub(r"^(?:create|add|new|register)\s+(?:a\s+|an\s+)?(?:business\s*partner|partner|bp)?\s*", "", non_empty[1], flags=re.IGNORECASE).strip()
            seg_a_clean = re.sub(r"\s+(?:business\s*partner|partner|company)$", "", seg_a, flags=re.IGNORECASE).strip()
            seg_b_clean = re.sub(r"\s+(?:business\s*partner|partner|company)$", "", seg_b, flags=re.IGNORECASE).strip()

            is_a_code = bool(re.match(r"^(?:(?:CV|BP|C|V|L)\d{1,8}|[A-Za-z]{1,4}\d{1,8})$", seg_a_clean, re.IGNORECASE))
            is_b_code = bool(re.match(r"^(?:(?:CV|BP|C|V|L)\d{1,8}|[A-Za-z]{1,4}\d{1,8})$", seg_b_clean, re.IGNORECASE))
            is_a_name = bool(re.match(r"^[A-Za-z\s&.,_-]{2,50}$", seg_a_clean) and not is_a_code)
            is_b_name = bool(re.match(r"^[A-Za-z\s&.,_-]{2,50}$", seg_b_clean) and not is_b_code)

            if is_a_code and is_b_name:
                if "CardCode" not in fields:
                    fields["CardCode"] = seg_a_clean.upper()
                if "CardName" not in fields:
                    fields["CardName"] = seg_b_clean
            elif is_b_code and is_a_name:
                if "CardCode" not in fields:
                    fields["CardCode"] = seg_b_clean.upper()
                if "CardName" not in fields:
                    fields["CardName"] = seg_a_clean

    for code_k in ["CardCode", "ItemCode", "WarehouseCode"]:
        if str(fields.get(code_k, "")).upper() in ["IS", "AS", "TO", "WITH", "THE", "A", "AN", "NEW", "ITEM", "CODE", "WAREHOUSE", "DEPOT", "THIS"]:
            fields.pop(code_k, None)

    return fields, errors


async def extract_fields_with_llm(message: str, entity: str) -> Dict[str, Any]:
    """
    Dynamically extracts master data creation fields from natural language text using LLM semantic extraction.
    """
    schema = MANDATORY_CREATION_SCHEMA.get(entity, {})
    valid_keys = list(schema.keys())
    prompt = f"""Extract SAP {entity} fields from prompt: "{message}"
Valid fields: {valid_keys}.
Output JSON only, e.g.: {{"CardCode": "C9901", "CardName": "Apex Global", "Address": "Mumbai", "GSTNo": "27AAACG0568M1Z2"}}"""
    try:
        raw = await nvidia_chat_service.generate(
            system_prompt="Extract JSON parameters for SAP.",
            user_prompt=prompt
        )
        clean = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()
        data = json.loads(clean)
        if isinstance(data, dict):
            norm_dict = {}
            for k, v in data.items():
                norm_k = normalize_field_name(entity, str(k)) or k
                if norm_k in valid_keys and v is not None and str(v).strip() != "":
                    is_v, n_val, _ = validate_field_value(entity, norm_k, v)
                    if is_v:
                        norm_dict[norm_k] = n_val
            return norm_dict
    except Exception as e:
        logger.debug(f"LLM natural language extraction note: {e}")
    return {}


async def extract_creation_session(
    history: Optional[List[Dict[str, Any]]],
    current_message: str
) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]], bool, List[str]]:
    """
    Accumulates creation fields across dialogue turns and validates them against the schema.
    Returns: (entity, accumulated_draft, missing_fields_spec, is_ready, validation_errors)
    """
    m_lower = current_message.strip().lower()

    explicit_bp = bool(re.search(r"\b(?:business\s*partner|partner|customer|vendor|supplier|bp)\b", m_lower) and re.search(r"\b(?:create|add|new|register|make|insert)\b", m_lower))
    explicit_item = bool(re.search(r"\b(?:item\s*master|item|items|product|sku|material)\b", m_lower) and re.search(r"\b(?:create|add|new|register|make|insert)\b", m_lower))
    explicit_wh = bool(re.search(r"\b(?:warehouse\s*master|warehouse|depot|storage)\b", m_lower) and re.search(r"\b(?:create|add|new|register|make|insert)\b", m_lower))

    active_draft_turn: Optional[Dict[str, Any]] = None
    if history:
        for turn in reversed(history):
            if turn.get("role") == "assistant":
                if turn.get("action") == "CREATE_DRAFT" and not turn.get("is_creation_ready"):
                    active_draft_turn = turn
                break

    if explicit_item:
        entity = "Items"
    elif explicit_wh:
        entity = "Warehouses"
    elif explicit_bp:
        entity = "BusinessPartners"
    elif active_draft_turn and active_draft_turn.get("entity") in ["BusinessPartners", "Items", "Warehouses"]:
        entity = active_draft_turn["entity"]
    else:
        entity = detect_entity(current_message)

    accumulated: Dict[str, Any] = {}
    prev_missing: List[Dict[str, Any]] = []

    is_new_command = (explicit_bp or explicit_item or explicit_wh) or any(m_lower.startswith(kw) for kw in ["start over", "reset", "clear draft"])

    # 1. Inherit from active draft if continuing the same entity
    if active_draft_turn and not is_new_command and active_draft_turn.get("entity") == entity:
        c_draft = active_draft_turn.get("creation_draft")
        if isinstance(c_draft, dict):
            accumulated = dict(c_draft)
        if active_draft_turn.get("missing_fields"):
            prev_missing = active_draft_turn.get("missing_fields")

    # 2. Extract new fields from current message (Fast-path deterministic)
    new_fields, val_errors = parse_creation_fields(current_message, entity)

    # 3. Dynamic Natural Language Extraction fallback if zero fields were found
    generic_inits = [
        "create a business partner", "create business partner", "create a customer", "create customer",
        "create a vendor", "create vendor", "create partner", "new business partner", "new customer",
        "create an item", "create item", "create item master", "create an item master", "add new item", "new item", "add item",
        "create a warehouse", "create warehouse", "register a warehouse", "register warehouse", "new warehouse", "add warehouse"
    ]
    is_generic_init = any(m_lower == g for g in generic_inits)

    if not new_fields and len(current_message.split()) >= 4 and not prev_missing and not is_generic_init:
        llm_extracted = await extract_fields_with_llm(current_message, entity)
        for k, v in llm_extracted.items():
            if k not in new_fields:
                new_fields[k] = v

    # 4. If user provided a direct standalone answer to one of the missing fields
    if not new_fields and prev_missing and len(val_errors) == 0:
        val_candidate = current_message.strip().strip("'\"")
        val_candidate_clean = re.sub(r"^(?:it\s+is|value\s+is|the\s+value\s+is|is|use|set\s+to)\s+", "", val_candidate, flags=re.IGNORECASE).strip()
        if val_candidate_clean.lower() not in ["cancel", "help", "what", "how", "create", "exit", "reset", "hi", "hello"]:
            # If candidate contains "and" or multiple tokens, attempt parsing multi-field response first
            if re.search(r"\band\b|,", val_candidate_clean, re.IGNORECASE):
                sub_f, sub_err = parse_creation_fields(val_candidate_clean, entity)
                if sub_f:
                    new_fields.update(sub_f)
                if sub_err:
                    val_errors.extend(sub_err)

            if not new_fields:
                matched_mf = None
                if entity == "BusinessPartners":
                    clean_low = val_candidate_clean.lower()
                    if any(kw in clean_low for kw in ["customer", "vendor", "supplier", "client", "lead"]):
                        matched_mf = "CardType"
                    elif re.match(r"^[CVL]?[A-Za-z0-9_-]{2,15}$", val_candidate_clean) and any(m["field"] == "CardCode" for m in prev_missing) and not any(kw in clean_low for kw in ["pvt", "ltd", "corp", "inc", "company", "logistics", "solutions", "enterprises", "industries", "services"]):
                        matched_mf = "CardCode"
                    elif any(m["field"] == "CardName" for m in prev_missing):
                        matched_mf = "CardName"

                if not matched_mf:
                    matched_mf = prev_missing[0]["field"]

                is_v, n_val, err = validate_field_value(entity, matched_mf, val_candidate_clean)
                if is_v:
                    new_fields[matched_mf] = n_val
                elif err:
                    val_errors.append(err)

    accumulated.update(new_fields)

    # 5. Auto-derivation & smart defaults:
    if entity == "BusinessPartners":
        gst = str(accumulated.get("GSTNo", "")).strip().upper()
        if gst and len(gst) == 15 and gst[:2].isdigit() and not accumulated.get("PANNo"):
            accumulated["PANNo"] = gst[2:12].upper()
        # Note: CardType, CardCode, and CardName are all strictly mandatory from the user.
        # No auto-defaulting of CardType without user input or confirmation.
    elif entity == "Items":
        if "InventoryUOM" not in accumulated and (accumulated.get("ItemCode") or accumulated.get("ItemName")):
            accumulated["InventoryUOM"] = "PCS"

    # 6. Compute remaining missing mandatory fields
    schema = MANDATORY_CREATION_SCHEMA.get(entity, {})
    missing_spec: List[Dict[str, Any]] = []
    for field_name, spec in schema.items():
        if spec.get("mandatory"):
            val = accumulated.get(field_name)
            if val is None or str(val).strip() == "":
                missing_spec.append({
                    "field": field_name,
                    "label": spec.get("label", field_name),
                    "example": spec.get("example", ""),
                    "reason": spec.get("reason", ""),
                    "max_length": spec.get("max_length")
                })

    is_ready = (len(missing_spec) == 0 and len(val_errors) == 0 and len(accumulated) > 0)
    return entity, accumulated, missing_spec, is_ready, val_errors
