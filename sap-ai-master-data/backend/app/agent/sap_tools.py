"""
Authoritative SAP Master Data Tools Specification & Dispatcher.
Defines OpenAI-compatible function calling schemas and execution handlers
for real-time SAP Business One Master Data operations.
"""
from typing import Any, Dict, List, Optional
import json
import re
from app.config import settings
from app.sap.client import sap_client
from app.sap.business_partners import SAPBusinessPartnersService
from app.sap.items import SAPItemsService
from app.sap.warehouses import SAPWarehousesService
from app.agent.field_mappings import (
    MANDATORY_CREATION_SCHEMA,
    normalize_field_name,
    validate_field_value,
)
import app.agent.specialized_queries as sq
from app.agent.tools import (
    execute_create_master_data,
    execute_field_update,
    execute_health_check,
    execute_specific_attribute_query,
)
from app.utils.logging import logger

SAP_AGENT_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "sap_query_master_data",
            "description": "Query and retrieve live master data records from SAP Service Layer for BusinessPartners, Items, or Warehouses with optional search, filtering, and limits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["BusinessPartners", "Items", "Warehouses"],
                        "description": "The SAP master data entity type"
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional search keyword (matches Code, Name, or Tax ID)"
                    },
                    "top": {
                        "type": "integer",
                        "description": "Number of records to retrieve (default: 20, max: 100)"
                    },
                    "custom_filter": {
                        "type": "string",
                        "description": "Optional OData $filter expression (e.g. \"CardType eq 'cCustomer'\" or \"Frozen eq 'tNO'\")"
                    }
                },
                "required": ["entity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_get_single_record",
            "description": "Fetch a specific master data record by its unique code (CardCode for BusinessPartner, ItemCode for Item, WarehouseCode for Warehouse).",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["BusinessPartners", "Items", "Warehouses"],
                        "description": "The SAP master data entity type"
                    },
                    "key": {
                        "type": "string",
                        "description": "The unique code identifier (e.g., 'C20000', 'ITM-001', '01')"
                    }
                },
                "required": ["entity", "key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_get_specific_attribute",
            "description": "Look up a specific attribute (address, phone, email, tax rate, UoM, balance, stock level, price, HSN, payment terms) for an SAP record.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["BusinessPartners", "Items", "Warehouses"],
                        "description": "The SAP master data entity type"
                    },
                    "key": {
                        "type": "string",
                        "description": "The unique code identifier (e.g. 'C20000', 'ITM-001')"
                    },
                    "attribute": {
                        "type": "string",
                        "description": "The attribute requested (e.g., 'address', 'phone', 'email', 'tax', 'stock', 'uom', 'hsn', 'balance', 'price')"
                    }
                },
                "required": ["entity", "key", "attribute"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_validate_and_draft_creation",
            "description": "Validate fields and manage an interactive creation draft for a new Business Partner, Item, or Warehouse. For BusinessPartners, CardCode (unique alphanumeric code like CV24 or C20099), CardType (cCustomer or cSupplier), and CardName (business name) are ALL strictly mandatory from the user. MUST be called whenever a user initiates or updates a master data creation request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["BusinessPartners", "Items", "Warehouses"],
                        "description": "The SAP entity being created"
                    },
                    "fields": {
                        "type": "object",
                        "description": "Field key-value pairs provided by the user so far (e.g. CardCode, CardName, CardType, ItemCode, ItemName, InventoryUOM, etc.)"
                    }
                },
                "required": ["entity", "fields"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_commit_create",
            "description": "Post a fully validated creation draft directly into SAP Business One Service Layer and record an audit log.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["BusinessPartners", "Items", "Warehouses"],
                        "description": "The SAP entity to create"
                    },
                    "data": {
                        "type": "object",
                        "description": "The complete validated creation payload"
                    }
                },
                "required": ["entity", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_propose_field_update",
            "description": "Validate and preview an update on an existing SAP record. Checks that the record exists and pre-validates values before applying changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity": {
                        "type": "string",
                        "enum": ["BusinessPartners", "Items", "Warehouses"],
                        "description": "The SAP entity type"
                    },
                    "key": {
                        "type": "string",
                        "description": "Target record code (e.g. 'C20000', 'ITM-001')"
                    },
                    "fields": {
                        "type": "object",
                        "description": "Field key-value pairs to update (e.g., {'Phone1': '9876543210', 'GSTNo': '27AABCU9603R1ZM'})"
                    }
                },
                "required": ["entity", "key", "fields"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_run_compliance_audit",
            "description": "Run domain compliance analytics and statutory audits on SAP master data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "audit_type": {
                        "type": "string",
                        "enum": [
                            "missing_gstin_pan",
                            "missing_hsn_uom",
                            "inactive_items_with_stock",
                            "inactive_bp_with_balance",
                            "overdue_aging",
                            "duplicate_items",
                            "duplicate_bp",
                            "min_max_items",
                            "ordered_committed_items",
                            "active_items",
                            "active_customers_vendors"
                        ],
                        "description": "The type of master data audit to perform"
                    }
                },
                "required": ["audit_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_health_check",
            "description": "Check real-time connectivity and status of SAP Business One Service Layer and active company database.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sap_search_knowledge_base",
            "description": "Search authoritative SAP Business One Technical Documentation, company master data governance rules (e.g. CINNTRA_DEMO_NEW company rules), SOP guidelines, mandatory policies, and Service Layer API schemas stored in the RAG ChromaDB knowledge base.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or question regarding company policies, master data guidelines, mandatory email rule, default currency, HSN codes, or SAP API standards"
                    },
                    "entity": {
                        "type": "string",
                        "enum": ["all", "BusinessPartners", "Items", "Warehouses", "CompanyRules"],
                        "description": "Optional domain filter"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


class SAPToolExecutor:
    """Dispatches tool calls to backend SAP services and returns structured observations."""

    @staticmethod
    async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "sap_query_master_data":
                entity = arguments.get("entity", "BusinessPartners")
                top = min(int(arguments.get("top", 20)), 100)
                search = arguments.get("search")
                custom_filter = arguments.get("custom_filter")
                res = await sap_client.get_live_records(
                    entity=entity,
                    top=top,
                    search=search,
                    custom_filter=custom_filter
                )
                return {
                    "success": True,
                    "entity": entity,
                    "total": res.get("total", len(res.get("records", []))),
                    "records": res.get("records", [])[:top]
                }

            elif tool_name == "sap_get_single_record":
                entity = arguments.get("entity", "BusinessPartners")
                key = str(arguments.get("key", "")).strip().upper()
                rec = await sap_client.get(entity, key=key)
                if not rec:
                    # Fallback to search if key was a name or partial
                    search_res = await sap_client.get_live_records(entity=entity, top=1, search=key)
                    if search_res.get("records"):
                        rec = search_res["records"][0]
                if rec:
                    return {"success": True, "entity": entity, "record": rec}
                return {"success": False, "entity": entity, "error": f"Record '{key}' not found in SAP."}

            elif tool_name == "sap_get_specific_attribute":
                entity = arguments.get("entity", "BusinessPartners")
                key = str(arguments.get("key", "")).strip()
                attr = str(arguments.get("attribute", "")).strip()
                fake_msg = f"what is the {attr} of {entity} {key}"
                res = await execute_specific_attribute_query(fake_msg)
                if res and res.get("success"):
                    return res
                # Direct fallback
                rec = await sap_client.get(entity, key=key)
                if rec:
                    val = rec.get(attr) or rec.get(normalize_field_name(entity, attr) or attr)
                    return {
                        "success": True,
                        "entity": entity,
                        "key": key,
                        "attribute": attr,
                        "value": str(val) if val is not None else "Not specified in SAP",
                        "record": rec
                    }
                return {"success": False, "error": f"Could not find attribute '{attr}' for '{key}'."}

            elif tool_name == "sap_validate_and_draft_creation":
                entity = arguments.get("entity", "BusinessPartners")
                raw_fields = dict(arguments.get("fields", {}))
                schema = MANDATORY_CREATION_SCHEMA.get(entity, {})

                # Defensive decomposition for BusinessPartners if code was passed combined (e.g. "cv02 and abc", "CV02ANDABC", etc.)
                if entity == "BusinessPartners":
                    from app.agent.slot_filling import parse_creation_fields
                    raw_code = str(raw_fields.get("CardCode", "")).strip()
                    if raw_code and (re.search(r"\band\b|\s+|is\s+code", raw_code, re.IGNORECASE) or re.search(r"^(?:CV|BP|C|V|L)\d{1,8}AND[A-Z0-9]+$", raw_code, re.IGNORECASE)):
                        cleaned_sub = re.sub(r"AND", " and ", raw_code, flags=re.IGNORECASE) if "AND" in raw_code else raw_code
                        decomposed, _ = parse_creation_fields(cleaned_sub, "BusinessPartners")
                        for dk, dv in decomposed.items():
                            if dk not in raw_fields or not raw_fields[dk]:
                                raw_fields[dk] = dv
                            elif dk == "CardCode" and dv != raw_code:
                                raw_fields["CardCode"] = dv

                validated_fields: Dict[str, Any] = {}
                validation_errors: List[str] = []

                for k, v in raw_fields.items():
                    norm_k = normalize_field_name(entity, str(k)) or k
                    is_v, n_val, err = validate_field_value(entity, norm_k, v)
                    if is_v:
                        validated_fields[norm_k] = n_val
                    elif err:
                        validation_errors.append(err)

                # Auto-derive PAN from GST if available
                if entity == "BusinessPartners" and validated_fields.get("GSTNo"):
                    gst = str(validated_fields["GSTNo"]).strip()
                    if len(gst) == 15 and "PANNo" not in validated_fields:
                        validated_fields["PANNo"] = gst[2:12].upper()

                # Check duplicate identifier
                key_field = "CardCode" if entity == "BusinessPartners" else ("ItemCode" if entity == "Items" else "WarehouseCode")
                key_val = str(validated_fields.get(key_field, "")).strip().upper()
                duplicate_warning = None

                if key_val:
                    already_exists = False
                    if entity == "BusinessPartners":
                        already_exists = await SAPBusinessPartnersService.check_card_exists(key_val)
                    elif entity == "Items":
                        already_exists = await SAPItemsService.check_item_exists(key_val)
                    elif entity == "Warehouses":
                        already_exists = await SAPWarehousesService.check_warehouse_exists(key_val)
                    if already_exists:
                        duplicate_warning = f"Code '{key_val}' already exists in SAP Business One. Please use a unique identifier."
                        validation_errors.append(duplicate_warning)

                # Check remaining missing mandatory fields
                missing_specs = []
                for field_name, spec in schema.items():
                    if spec.get("mandatory"):
                        cur_val = validated_fields.get(field_name)
                        if cur_val is None or str(cur_val).strip() == "":
                            item_spec = dict(spec)
                            item_spec["field"] = field_name
                            missing_specs.append(item_spec)

                is_ready = (len(missing_specs) == 0 and not duplicate_warning)

                return {
                    "success": True,
                    "entity": entity,
                    "draft": validated_fields,
                    "missing_fields": missing_specs,
                    "is_ready": is_ready,
                    "validation_errors": validation_errors
                }

            elif tool_name == "sap_propose_field_update":
                entity = arguments.get("entity", "BusinessPartners")
                key = str(arguments.get("key", "")).strip().upper()
                fields = arguments.get("fields", {})
                res = await execute_field_update(entity=entity, key=key, fields=fields, prompt="Update via AI Agent")
                return res

            elif tool_name == "sap_commit_create":
                entity = arguments.get("entity", "BusinessPartners")
                data = arguments.get("data", {})
                return await execute_create_master_data(entity=entity, data=data)

            elif tool_name == "sap_run_compliance_audit":
                audit_type = arguments.get("audit_type", "")
                dispatcher = {
                    "missing_gstin_pan": sq.execute_missing_incorrect_gstin_pan,
                    "missing_hsn_uom": sq.execute_missing_hsn_or_uom,
                    "inactive_items_with_stock": sq.execute_inactive_items_with_stock,
                    "inactive_bp_with_balance": sq.execute_inactive_bp_with_balance,
                    "overdue_aging": sq.execute_overdue_aging_bp,
                    "duplicate_items": sq.execute_duplicate_items,
                    "duplicate_bp": sq.execute_duplicate_bp,
                    "min_max_items": sq.execute_min_max_items,
                    "ordered_committed_items": sq.execute_ordered_committed_items,
                    "active_items": sq.execute_active_items,
                    "active_customers_vendors": sq.execute_active_customers_vendors,
                }
                fn = dispatcher.get(audit_type)
                if fn:
                    return await fn(f"audit {audit_type}")
                return {"success": False, "error": f"Unknown audit type '{audit_type}'"}

            elif tool_name == "sap_health_check":
                return await execute_health_check()

            elif tool_name == "sap_search_knowledge_base":
                from app.rag.retriever import retriever
                query = str(arguments.get("query", "")).strip()
                entity_arg = arguments.get("entity")
                if entity_arg in ["all", None]:
                    entity_arg = None
                chunks = retriever.search(query=query, top_k=4, entity=entity_arg)
                return {
                    "success": True,
                    "query": query,
                    "results_count": len(chunks),
                    "knowledge_chunks": [
                        {
                            "source": c.get("source", "SAP Documentation"),
                            "section": c.get("metadata", {}).get("section", "General"),
                            "content": c.get("content", ""),
                            "score": c.get("score", 0.0)
                        }
                        for c in chunks
                    ]
                }

            else:
                return {"success": False, "error": f"Unknown tool: '{tool_name}'"}

        except Exception as e:
            logger.error(f"Error executing SAP tool '{tool_name}': {e}")
            return {"success": False, "error": str(e)}
