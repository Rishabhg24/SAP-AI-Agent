"""
Autonomous SAP ReAct Agent Runtime.
Executes iterative Reason-and-Act (ReAct) loops using native OpenAI-compatible tool calling
with NVIDIA Nemotron/Llama models against live SAP Business One Service Layer.
"""
from typing import Any, Dict, List, Optional
import json
import re
from app.config import settings
from app.services.chat_service import nvidia_chat_service
from app.agent.sap_tools import SAP_AGENT_TOOLS, SAPToolExecutor
from app.utils.logging import logger

SYSTEM_PROMPT = f"""You are the authoritative Autonomous SAP Master Data AI Agent for SAP Business One.
Connected live to SAP Service Layer (Company DB: `{settings.sap_company_db}`).

You act as a real-world enterprise AI agent with full natural language understanding, real-time live data execution, and integrated RAG knowledge retrieval.

Your capabilities & responsibilities:
1. MASTER DATA QUERIES & AUDITS:
   - Retrieve real-time Business Partners, Items, and Warehouses. Provide clear markdown tables and metrics.
   - For statutory data quality and audits (missing GSTIN/PAN, missing HSN/UoM, inactive items with stock, overdue aging), invoke `sap_run_compliance_audit`.
2. GRANULAR ATTRIBUTES:
   - Answer precise questions about specific attributes (balances, addresses, phone, GSTIN, PAN, tax rates, stock, price, UoM, HSN) using `sap_get_specific_attribute`.
3. CONVERSATIONAL CREATION (SLOT-FILLING & INPUT DISAMBIGUATION):
   - When a user wants to create master data, collect details and manage the draft iteratively.
   - MANDATORY BUSINESS PARTNER CREATION REQUIREMENTS:
     For Business Partners (`BusinessPartners`), YOU MUST COLLECT ALL THREE OF THE FOLLOWING FIELDS FROM THE USER BEFORE MARKING THE DRAFT READY:
     1. `CardCode`: Alphanumeric unique partner code (e.g. CV24, CV02, C20099, V10099). Maximum 15 characters.
     2. `CardType`: Business partner classification: Customer (`cCustomer`) or Vendor / Supplier (`cSupplier`) or Lead (`cLid`).
     3. `CardName`: Legal entity or business name (e.g. Cinntra Global Logistics Ltd, ABC).
     CRITICAL: Do NOT assume or auto-fill `CardType` without the user explicitly stating or confirming whether they are a Customer or Vendor. If any of CardCode, CardType, or CardName is missing, ask the user for the missing fields.
   - For Items (`Items`): Mandatory fields are `ItemCode` and `ItemName`. `InventoryUOM` defaults to PCS.
   - For Warehouses (`Warehouses`): Mandatory field is `WarehouseCode`.
   - AGENT THINKING & INPUT DISAMBIGUATION:
     Users frequently provide shorthand inputs or informal statements, for example:
       * "cv24 is code and abc business partner"
       * "cv02 and abc"
       * "cv24 and abc"
       * "code cv24 and partner abc"
       * "partner is abc and code is cv24"
       * "cv24 is code, abc is name, customer"
     RECOGNIZE THAT:
       * Alphanumeric identifiers (e.g. `cv24`, `cv02`, `c20099`, `v10099`, `bp01`, `c01`) represent `CardCode`!
         CRITICAL: NEVER combine or concatenate code and name into a single string (e.g. NEVER make 'CV02ANDABC'). The code is strictly the code portion (e.g. 'CV24' or 'CV02').
       * Company / Partner names (e.g. `abc`, `Cinntra`, `Acme Global`) represent `CardName`!
         Words like 'business partner', 'partner', 'company', 'bp' indicate the entity role, NOT part of the company name.
       * Partner classification words: 'customer', 'client' -> `cCustomer`; 'vendor', 'supplier' -> `cSupplier`; 'lead' -> `cLid`.
   - ALWAYS invoke `sap_validate_and_draft_creation` with the extracted fields so they are validated and checked for duplicates in SAP.
     For example, for "cv24 is code and abc business partner":
     Call `sap_validate_and_draft_creation(entity='BusinessPartners', fields={{"CardCode": "CV24", "CardName": "abc"}})`.
     Since `CardType` is still missing, inform the user that code `CV24` and name `abc` are recorded, and ask whether this partner is a Customer or a Vendor!
   - When all mandatory fields (CardCode, CardType, CardName for BP) are ready and verified, inform the user that the draft is ready and they can click "Post to SAP" or say "confirm".
   - If the user confirms a ready draft (e.g. "confirm", "post to sap", "proceed"), invoke `sap_commit_create`.
4. FIELD UPDATES:
   - When asked to update a record, use `sap_propose_field_update` to validate and execute the change with audit tracking.
   - If the update fails because the record does not exist or SQL rejects inserting NULL into CardCode, explain clearly to the user in friendly language that the record does not exist in SAP and must be created first before updating. Do not dump raw ODBC/SQL error traces.
5. KNOWLEDGE BASE & COMPANY GOVERNANCE (RAG):
   - When asked about company governance rules, SOP guidelines, business policies (e.g. mandatory email rule, default currency, uppercase codes), or SAP technical schemas, ALWAYS invoke `sap_search_knowledge_base` to retrieve grounded documentation from the ChromaDB knowledge base.
   - Synthesize the retrieved documentation into an authoritative, direct answer, citing the document name and section.
6. SYSTEM HEALTH:
   - When asked if SAP is up, connected, or healthy, invoke `sap_health_check`.
7. GREETINGS, CAPABILITIES & GENERAL DIALOGUE:
   - When the user greets you ("hi", "hello", "hey", "hola", "namaste", "good morning", etc.) or asks what you can do ("help", "who are you", "what are your capabilities"), introduce yourself warmly and conversationally as the Autonomous SAP Master Data AI Agent for SAP Business One (`{settings.sap_company_db}`).
   - Describe your core capabilities clearly:
     * Interactive Master Data Creation (Business Partners, Items, Warehouses) with intelligent slot-filling and validation
     * Granular attribute queries (addresses, tax rates, stock, price, UoM, HSN)
     * Universal field updates with audit tracking
     * Live master data queries and compliance audits (missing GSTIN/PAN, inactive items with stock, overdue aging)
     * Company SOP and governance policies retrieval via RAG
     * SAP Service Layer system health monitoring
   - Suggest 2-3 specific, actionable examples they can try.
8. CONFIRMATION & POSTING:
   - If there is an active creation draft that is ready (`is_ready=True`) and the user says "confirm", "proceed", "post to sap", "yes", or "submit", invoke `sap_commit_create(entity, data)` immediately.
   - Once committed or if an error occurs, synthesize the outcome dynamically, highlighting the created identifier or explaining the error clearly with recommended next steps.

RULES & STYLE:
- ZERO HARDCODED RESPONSES: Every single response you produce MUST be your own original, dynamically generated explanation in natural, professional English. Never output canned, mechanical, or repetitive templates.
- NEVER hallucinate SAP records or invent fake values. Always use your tools to query, validate, or look up information.
- Provide real-time, concise, structured responses using GitHub markdown (tables, bold highlights, bullet points).
- Understand natural language prompts flexibly, including colloquial phrasings, partial information, and multi-sentence commands.
"""

class ReActAgent:
    """Executes ReAct multi-turn loop with native function calling."""

    @classmethod
    async def run(
        cls,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full autonomous ReAct agent loop.
        """
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

        last_assistant_turn: Optional[Dict[str, Any]] = None
        cached_draft: Optional[Dict[str, Any]] = None
        cached_draft_entity: Optional[str] = None
        cached_draft_ready: bool = False

        # Build conversation context from previous turns
        if history:
            for turn in history[-6:]:  # Keep recent history within context window
                role = turn.get("role", "user")
                content = turn.get("content") or turn.get("reply") or ""
                if role == "assistant":
                    last_assistant_turn = turn
                    if turn.get("creation_draft"):
                        cached_draft = turn.get("creation_draft")
                        cached_draft_entity = turn.get("entity")
                        cached_draft_ready = bool(turn.get("is_creation_ready"))
                if content:
                    messages.append({"role": role, "content": str(content)})

        # Remove trailing duplicate user message if history payload already included current prompt
        if len(messages) > 1 and messages[-1].get("role") == "user" and messages[-1].get("content") == message:
            messages.pop()

        m_lower = message.strip().lower()
        new_entity_init = None
        if re.search(r"\b(create|add|new|register)\s+(?:an?\s+)?(?:item|product|item master)\b", m_lower) or m_lower in ["create item master", "create an item", "new item", "add item", "create item"]:
            new_entity_init = "Items"
        elif re.search(r"\b(create|add|new|register)\s+(?:an?\s+)?(?:customer|vendor|supplier|business partner|bp|partner)\b", m_lower) or m_lower in ["create business partner", "create bp", "new customer", "new vendor", "add customer", "add vendor"]:
            new_entity_init = "BusinessPartners"
        elif re.search(r"\b(create|add|new|register)\s+(?:an?\s+)?(?:warehouse|depot)\b", m_lower) or m_lower in ["create warehouse", "new warehouse", "add warehouse"]:
            new_entity_init = "Warehouses"

        # If switching entity type during creation, isolate and clear previous entity draft
        if new_entity_init and cached_draft_entity and new_entity_init != cached_draft_entity:
            cached_draft = None
            cached_draft_entity = None
            cached_draft_ready = False

        # Append current user instruction with draft context hint if in an active creation session
        user_content = message
        if cached_draft and not any(kw in m_lower for kw in ["list all", "top 20", "cancel", "health", "give me top"]):
            user_content = (
                f"{message}\n\n[System Context: Active {cached_draft_entity} Creation Draft: "
                f"{json.dumps(cached_draft)}, is_ready={cached_draft_ready}]"
            )

        messages.append({"role": "user", "content": user_content})

        # Track state captured by tools executed during this turn
        captured_entity: Optional[str] = new_entity_init or cached_draft_entity
        captured_action: str = "EXPLAIN"
        captured_records: List[Dict[str, Any]] = []
        captured_total: int = 0
        captured_draft: Optional[Dict[str, Any]] = cached_draft
        captured_missing_fields: List[Dict[str, Any]] = []
        captured_is_ready: bool = cached_draft_ready
        captured_update_result: Optional[Dict[str, Any]] = None
        captured_granular_answer: Optional[Dict[str, Any]] = None
        captured_suggestions: List[str] = []
        captured_sources: List[Dict[str, Any]] = []

        max_iterations = 4
        current_iteration = 0

        while current_iteration < max_iterations:
            current_iteration += 1

            try:
                assistant_msg = await nvidia_chat_service.chat_completion(
                    messages=messages,
                    tools=SAP_AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=0.1
                )
            except Exception as e:
                logger.error(f"ReAct agent chat completion error: {e}")
                # Fallback to standard agent service if LLM API is unavailable
                break

            tool_calls = getattr(assistant_msg, "tool_calls", None)

            # If no tools called, we've reached final textual response
            if not tool_calls:
                final_content = assistant_msg.content or ""
                # If user asked to create an entity and draft tool was not invoked, parse message fields and initialize draft
                if new_entity_init and not captured_draft:
                    from app.agent.slot_filling import parse_creation_fields
                    fb_fields, _ = parse_creation_fields(message, new_entity_init)
                    init_res = await SAPToolExecutor.execute_tool("sap_validate_and_draft_creation", {"entity": new_entity_init, "fields": fb_fields})
                    captured_entity = new_entity_init
                    captured_draft = init_res.get("draft", {})
                    captured_missing_fields = init_res.get("missing_fields", [])
                    captured_is_ready = bool(init_res.get("is_ready", False))
                    captured_action = "CREATE_READY" if captured_is_ready else "CREATE_DRAFT"
                elif captured_draft and captured_action == "EXPLAIN":
                    captured_action = "CREATE_READY" if captured_is_ready else "CREATE_DRAFT"

                return cls._format_response(
                    reply=final_content,
                    action=captured_action,
                    entity=captured_entity,
                    records=captured_records,
                    total=captured_total or len(captured_records),
                    creation_draft=captured_draft,
                    missing_fields=captured_missing_fields,
                    is_creation_ready=captured_is_ready,
                    update_result=captured_update_result,
                    granular_answer=captured_granular_answer,
                    suggestions=captured_suggestions,
                    prompt=message,
                    sources=captured_sources
                )

            # Process tool calls
            # 1. Append assistant message with tool calls to history
            assistant_dict: Dict[str, Any] = {
                "role": "assistant",
                "content": assistant_msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            }
            messages.append(assistant_dict)

            # 2. Execute each tool and feed results back to model
            for tc in tool_calls:
                fn_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                except Exception:
                    args = {}

                logger.info(f"ReAct Agent executing tool '{fn_name}' with args: {args}")
                tool_output = await SAPToolExecutor.execute_tool(fn_name, args)

                # Capture state for UI rendering
                if fn_name == "sap_query_master_data":
                    if captured_action not in ["CREATE_READY", "CREATE_DRAFT", "CREATE_SUCCESS"]:
                        captured_action = "QUERY"
                    captured_entity = tool_output.get("entity", captured_entity)
                    captured_records = tool_output.get("records", [])
                    captured_total = tool_output.get("total", len(captured_records))

                elif fn_name == "sap_get_single_record":
                    if captured_action not in ["CREATE_READY", "CREATE_DRAFT", "CREATE_SUCCESS"]:
                        captured_action = "QUERY"
                    captured_entity = tool_output.get("entity", captured_entity)
                    rec = tool_output.get("record")
                    if rec:
                        captured_records = [rec]
                        captured_total = 1

                elif fn_name == "sap_get_specific_attribute":
                    if captured_action not in ["CREATE_READY", "CREATE_DRAFT", "CREATE_SUCCESS"]:
                        captured_action = "QUERY"
                    captured_entity = tool_output.get("entity", captured_entity)
                    captured_granular_answer = tool_output.get("granular_answer") or {
                        "attribute": tool_output.get("attribute", ""),
                        "value": tool_output.get("value", ""),
                        "code": tool_output.get("key", ""),
                        "name": str(tool_output.get("record", {}).get("CardName") or tool_output.get("record", {}).get("ItemName") or "")
                    }
                    if tool_output.get("record"):
                        captured_records = [tool_output["record"]]
                        captured_total = 1

                elif fn_name == "sap_validate_and_draft_creation":
                    captured_entity = tool_output.get("entity", captured_entity)
                    captured_draft = tool_output.get("draft", {})
                    captured_missing_fields = tool_output.get("missing_fields", [])
                    captured_is_ready = bool(tool_output.get("is_ready", False))
                    captured_action = "CREATE_READY" if captured_is_ready else "CREATE_DRAFT"

                elif fn_name == "sap_commit_create":
                    captured_action = "CREATE_SUCCESS" if tool_output.get("success") else "CREATE_FAILED"
                    captured_entity = tool_output.get("entity", captured_entity)
                    captured_draft = tool_output.get("creation_draft")
                    captured_is_ready = True
                    if tool_output.get("records"):
                        captured_records = tool_output["records"]

                elif fn_name == "sap_propose_field_update":
                    captured_action = "UPDATE"
                    captured_entity = tool_output.get("entity", captured_entity)
                    captured_update_result = tool_output.get("update_result")
                    if tool_output.get("records"):
                        captured_records = tool_output["records"]
                        captured_total = len(captured_records)

                elif fn_name == "sap_run_compliance_audit":
                    captured_action = "QUERY"
                    captured_entity = tool_output.get("entity", captured_entity)
                    captured_records = tool_output.get("records", [])
                    captured_total = tool_output.get("total", len(captured_records))

                elif fn_name == "sap_health_check":
                    captured_action = "HEALTH"

                elif fn_name == "sap_search_knowledge_base":
                    captured_action = "EXPLAIN"
                    for k in tool_output.get("knowledge_chunks", []):
                        captured_sources.append({
                            "document": k.get("source", "SAP Documentation"),
                            "section": k.get("section", "General"),
                            "score": k.get("score", 0.0)
                        })

                # Append tool observation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": fn_name,
                    "content": json.dumps(tool_output)
                })

        # Dynamic AI model synthesis if loop reached maximum iterations
        synth_reply = ""
        try:
            synth_reply = await nvidia_chat_service.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=(
                    f"User message: '{message}'.\n"
                    f"Action: {captured_action}, Entity: {captured_entity}.\n"
                    f"Records count: {len(captured_records)}.\n"
                    "Provide a helpful, complete markdown summary of the result and next steps for the user."
                )
            )
        except Exception as e_synth:
            logger.warning(f"Fallback generation note: {e_synth}")
            synth_reply = f"Operation for {captured_entity or 'SAP master data'} processed. How would you like to proceed next?"

        return cls._format_response(
            reply=synth_reply,
            action=captured_action,
            entity=captured_entity,
            records=captured_records,
            total=captured_total,
            creation_draft=captured_draft,
            missing_fields=captured_missing_fields,
            is_creation_ready=captured_is_ready,
            update_result=captured_update_result,
            granular_answer=captured_granular_answer,
            suggestions=captured_suggestions,
            prompt=message,
            sources=captured_sources
        )

    @classmethod
    def _format_response(
        cls,
        reply: str,
        action: str,
        entity: Optional[str] = None,
        records: Optional[List[Dict[str, Any]]] = None,
        total: int = 0,
        creation_draft: Optional[Dict[str, Any]] = None,
        missing_fields: Optional[List[Dict[str, Any]]] = None,
        is_creation_ready: bool = False,
        update_result: Optional[Dict[str, Any]] = None,
        granular_answer: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        prompt: str = "",
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Ensures unified response schema matching frontend state model."""
        recs = records or []
        suggs = suggestions or []
        if not suggs:
            if action in ["CREATE_DRAFT", "CREATE_READY"]:
                if is_creation_ready:
                    suggs = ["Post to SAP", "Cancel"]
                else:
                    suggs = [f"Provide {m.get('label')}" for m in (missing_fields or [])[:2]]
            elif action == "QUERY" and recs:
                code_k = recs[0].get("CardCode") or recs[0].get("ItemCode") or recs[0].get("WarehouseCode")
                if code_k:
                    suggs = [f"Show details of {code_k}", "Give me top 20 Business Partners", "Check SAP Health"]
            elif any(w in (prompt or "").lower() for w in ["bye", "goodbye", "cya", "see you", "farewell"]):
                suggs = ["Check SAP Health", "Create a Business Partner", "Top 20 Items"]
            elif any(w in (prompt or "").lower() for w in ["thank", "thanks", "thx", "appreciate"]):
                suggs = ["Give me top 20 Business Partners", "Check SAP Health", "Create a Business Partner"]
            elif any(w in (prompt or "").lower() for w in ["hi", "hello", "hey", "hola", "namaste", "good morning", "good evening"]):
                suggs = ["Create a Business Partner", "Give me top 20 Business Partners", "Check SAP Health", "List all Warehouses"]
            else:
                suggs = ["Create a Business Partner", "Give me top 20 Business Partners", "Check SAP Health"]

        return {
            "success": True,
            "reply": reply,
            "action": action,
            "entity": entity,
            "records": recs,
            "total": total or len(recs),
            "update_result": update_result,
            "creation_draft": creation_draft,
            "missing_fields": missing_fields or [],
            "is_creation_ready": is_creation_ready,
            "granular_answer": granular_answer,
            "suggestions": suggs,
            "prompt": prompt,
            "sources": sources or []
        }


react_agent = ReActAgent()
