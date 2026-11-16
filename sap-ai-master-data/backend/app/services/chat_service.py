"""
NVIDIA Hosted LLM Chat Service.
Communicates with NVIDIA API at https://integrate.api.nvidia.com/v1/chat/completions.
Uses model nvidia/nemotron-3.5-lightning-30b-a3b with low temperature.
"""
from typing import Any, Dict, List, Optional
import httpx
from openai import AsyncOpenAI
from app.config import settings
from app.rag.prompts import STRICT_SAP_SYSTEM_PROMPT
from app.utils.logging import logger

class NVIDIAChatService:
    @property
    def base_url(self) -> str:
        return settings.nvidia_base_url.rstrip("/")

    @property
    def model(self) -> str:
        return settings.nvidia_model

    @property
    def temperature(self) -> float:
        return settings.nvidia_temperature

    @property
    def max_tokens(self) -> int:
        return settings.nvidia_max_tokens

    @property
    def timeout_seconds(self) -> float:
        return getattr(settings, "nvidia_timeout_seconds", 45.0)

    def _get_client(self) -> AsyncOpenAI:
        api_key = settings.nvidia_api_key or "placeholder_key"
        return AsyncOpenAI(
            base_url=self.base_url,
            api_key=api_key,
            max_retries=2,
            timeout=self.timeout_seconds
        )

    def _sanitize_response(self, text: str) -> str:
        """Strip chain-of-thought or reasoning preludes leaked by the model."""
        import re
        # Remove XML-style thinking tags
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Strip 'Here's a thinking process:' blocks if present
        if "Here's a thinking process:" in cleaned:
            parts = re.split(r"(?:Here's a thinking process:.*?)(?=\n\n(?:[A-Z]|\*|Based on|According to|To create|In SAP))", cleaned, flags=re.DOTALL)
            if len(parts) > 1 and parts[-1].strip():
                cleaned = parts[-1].strip()
        return cleaned.strip()

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Any = "auto",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """
        Primary LLM interface with full Native Tool Calling support.
        Returns the raw assistant ChatCompletionMessage (content, tool_calls, etc.)
        """
        if not settings.is_nvidia_configured:
            raise RuntimeError("NVIDIA API key is not configured.")

        client = self._get_client()
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = tool_choice

        try:
            response = await client.chat.completions.create(**params)
            msg = response.choices[0].message
            if msg.content:
                msg.content = self._sanitize_response(msg.content)
            return msg
        except Exception as e:
            err_msg = str(e).lower()
            # If tool calling failed due to parameter incompatibility, retry without tools
            if tools and any(k in err_msg for k in ("tool", "tools", "unrecognized", "400", "422", "bad request")):
                logger.warning(f"NVIDIA tool call failed ({e}). Retrying standard completion without tools...")
                params_fallback = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": tokens,
                }
                try:
                    fb_res = await client.chat.completions.create(**params_fallback)
                    msg_fb = fb_res.choices[0].message
                    if msg_fb.content:
                        msg_fb.content = self._sanitize_response(msg_fb.content)
                    return msg_fb
                except Exception as e_fb:
                    logger.error(f"NVIDIA retry completion also failed: {e_fb}")
                    raise e_fb
            logger.error(f"NVIDIA Chat Completion failed: {e}")
            raise e

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = ""
    ) -> str:
        """
        Generate grounded conversational response using NVIDIA hosted API.
        Enforces system prompts and low temperature.
        """
        full_system = system_prompt or STRICT_SAP_SYSTEM_PROMPT
        if context:
            full_system += f"\n\nAuthoritative SAP Documentation Context:\n{context}"

        if not settings.is_nvidia_configured:
            # Safe local fallback when API key is a placeholder
            logger.info("NVIDIA API key not configured. Generating deterministic fallback response.")
            return self._deterministic_fallback_response(user_prompt, context)

        try:
            client = self._get_client()
            params: Dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            # Disable reasoning/thinking tokens on Nemotron when generating plain text
            if "nemotron" in self.model.lower():
                params["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

            try:
                response = await client.chat.completions.create(**params)
            except Exception as call_err:
                err_msg = str(call_err).lower()
                if "extra_body" in params and any(k in err_msg for k in ("extra_body", "chat_template_kwargs", "unrecognized", "400", "422")):
                    params.pop("extra_body", None)
                    response = await client.chat.completions.create(**params)
                else:
                    raise call_err

            raw_text = response.choices[0].message.content or ""
            return self._sanitize_response(raw_text)
        except Exception as e:
            logger.warning(f"NVIDIA API request failed or timed out: {e}. Falling back to rule-based response.")
            return self._deterministic_fallback_response(user_prompt, context)

    def _deterministic_fallback_response(self, user_prompt: str, context: str) -> str:
        """
        Local, intelligent, rule-based fallback when NVIDIA API key is unavailable, offline, or times out.
        Accurately recognizes conversational dialogues (greetings, farewells, gratitude, identity, capabilities),
        specific entity requests, and SAP master data topics.
        """
        import re

        # Extract the user's actual question / input if formatted with RAG or instruction wrappers
        query_part = user_prompt.strip()
        m_said = re.search(r"The user said:\s*['\"](.*?)['\"]", query_part, re.DOTALL | re.IGNORECASE)
        if m_said:
            query_part = m_said.group(1).strip()
        elif "Question:" in user_prompt:
            query_part = user_prompt.split("Question:", 1)[1].strip()
        elif "User message:" in user_prompt:
            query_part = user_prompt.split("User message:", 1)[1].strip()
        elif "User prompt:" in user_prompt:
            query_part = user_prompt.split("User prompt:", 1)[1].strip()

        prompt_clean = query_part.strip().strip("'\"")
        prompt_lower = prompt_clean.lower()
        company_db = getattr(settings, "sap_company_db", "CINNTRA_DEMO_NEW") or "CINNTRA_DEMO_NEW"

        # 1. Farewells / Goodbyes
        farewell_patterns = [
            r"\b(?:bye|goodbye|cya|see\s+ya|see\s+you|farewell|signing\s+off|catch\s+you\s+later)\b",
            r"\b(?:have\s+a\s+(?:great|nice|good)\s+day|good\s*night|take\s*care)\b",
            r"^(?:bye|goodbye|exit|quit|close|done)[!.]*$"
        ]
        if any(re.search(pat, prompt_lower) for pat in farewell_patterns):
            return (
                "Goodbye! 👋 Have a wonderful day!\n\n"
                "Whenever you need to search SAP master data, register new records, or run compliance audits, "
                "I'll be right here to assist you. Take care!"
            )

        # 2. Greetings
        greeting_patterns = [
            r"^(?:hi|hello|hey|hola|namaste|heya|howdy|sup|yo|greetings|good\s+(?:morning|afternoon|evening|day))[!.]*$",
            r"\b(?:hello|hey|good\s+morning|good\s+afternoon|good\s+evening)\b"
        ]
        if any(re.search(pat, prompt_lower) for pat in greeting_patterns):
            return (
                f"Hello! 👋 I am your Autonomous SAP AI Master Data Assistant connected to SAP Business One (`{company_db}`).\n\n"
                "How can I assist you today? You can ask me to:\n"
                "• **Query Master Data**: *'Give me top 20 Business Partners'* or *'Top 20 Items from SAP'*\n"
                "• **Create Master Data**: *'Create a Business Partner'* or *'Create an Item'*\n"
                "• **Look Up Attributes**: *'What is the address of customer C20000?'*\n"
                "• **Update Records**: *'Update phone number for customer C20000'*\n"
                "• **System Health**: *'Check SAP health'*"
            )

        # 3. Gratitude / Thanks
        thanks_patterns = [
            r"\b(?:thank\s+you|thanks|thx|appreciate\s+it|thank\s+u)\b",
            r"\b(?:great\s+job|awesome|perfect|well\s+done|good\s+job|nice\s+work|superb)\b"
        ]
        if any(re.search(pat, prompt_lower) for pat in thanks_patterns):
            return (
                "You're very welcome! 😊 Always happy to help.\n\n"
                "Let me know if you would like to view live records, update any attributes, or create new master data in SAP."
            )

        # 4. Affirmations / Acknowledgements
        ack_patterns = [
            r"\b(?:ok|okay|sure|got\s+it|understood|alright|all\s+right|cool|fine|sounds\s+good)\b",
            r"^(?:yes|yep|yeah|no|nope|k)[!.]*$"
        ]
        if any(re.search(pat, prompt_lower) for pat in ack_patterns):
            return (
                "Understood! 👍 What would you like to explore next? You can inspect live master data, "
                "run compliance checks, or create a new Business Partner or Item."
            )

        # 5. Identity / Capabilities / Help
        capability_patterns = [
            r"\b(?:who\s+are\s+you|what\s+can\s+you\s+do|help|what\s+are\s+your\s+capabilities|features|commands|how\s+do\s+you\s+work|what\s+is\s+this)\b"
        ]
        if any(re.search(pat, prompt_lower) for pat in capability_patterns):
            return (
                f"I am your Autonomous SAP AI Agent for SAP Business One (`{company_db}`).\n\n"
                "Here are my core capabilities:\n\n"
                "1. 🔍 **Live Master Data Queries & Filtering**\n"
                "   • View Items, Business Partners, or Warehouses with real-time filters (e.g. *'customers in Delhi'*, *'items with price > 500'*).\n\n"
                "2. 📋 **Interactive Master Data Creation**\n"
                "   • Conversational creation with slot-filling, automatic field validation, and 1-click posting to SAP Service Layer.\n\n"
                "3. ✏️ **Granular Attribute Queries & Field Updates**\n"
                "   • Query: *'What is the address of customer C20000?'* or *'What is the tax rate of item ITM-001?'*\n"
                "   • Update: *'Update phone number to 9876543210 for customer C20000'*\n\n"
                "4. 🏥 **System Health & Statutory Compliance**\n"
                "   • Verify live SAP Service Layer connectivity and audit missing GSTIN, PAN, or HSN details."
            )

        # 6. SAP Entities Specific Guidance
        if any(k in prompt_lower for k in ["item", "oitm", "product", "sku", "inventory"]):
            return (
                "**SAP Item Master Data (OITM) Overview:**\n\n"
                "• **Mandatory Fields**: `ItemCode` (unique identifier, up to 50 alphanumeric characters) and `ItemName` (description, up to 100 characters).\n"
                "• **Grouping & Attributes**: `ItemsGroupCode` (category), `InventoryUOM` (default: PCS), Sales/Purchase/Inventory item flags.\n"
                "• **Statutory & Financials**: `HSN` code, GST tax rates, and valuation methods.\n\n"
                "💡 *Try asking: 'Top 20 Items from SAP' or 'Create an Item'*."
            )
        elif any(k in prompt_lower for k in ["partner", "vendor", "customer", "ocrd", "supplier", "bp"]):
            return (
                "**SAP Business Partner Master Data (OCRD) Overview:**\n\n"
                "• **Mandatory Fields**: `CardCode` (unique ID, up to 15 characters, e.g. `C20001` or `V10001`), `CardName` (legal name), and `CardType` (`cCustomer` for clients, `cSupplier` for vendors).\n"
                "• **Contact & Statutory**: `Phone1`, `EmailAddress`, `FederalTaxID` (15-character GSTIN), and `Address` / `City` / `State`.\n\n"
                "💡 *Try asking: 'Give me top 20 Business Partners' or 'Create a Business Partner'*."
            )
        elif any(k in prompt_lower for k in ["warehouse", "owhs", "depot", "godown"]):
            return (
                "**SAP Warehouse Master Data (OWHS) Overview:**\n\n"
                "• **Mandatory Fields**: `WarehouseCode` (unique code, up to 8 characters, e.g. `01`, `WH01`) and `WarehouseName`.\n"
                "• **Optional Flags**: Location, Bin activation (`EnableBinLocations`), and drop-ship configuration.\n\n"
                "💡 *Try asking: 'List all Warehouses' or 'Create a Warehouse'*."
            )
        elif any(k in prompt_lower for k in ["health", "status", "ping", "connected", "connection"]):
            return (
                f"SAP Business One Service Layer is configured for Company DB `{company_db}`. "
                "You can say *'Check SAP Health'* to test real-time connectivity and retrieve live record counts."
            )
        elif context:
            snippet = context.strip().split("\n")[0]
            return f"According to SAP documentation: {snippet}"
        else:
            return (
                f"I received your request: **'{prompt_clean}'**.\n\n"
                f"As your Autonomous SAP Master Data Assistant connected to `{company_db}`, "
                "I can help you search records, check specific attributes, create new master data entries, or update existing fields.\n\n"
                "How would you like to proceed?"
            )

    async def transform_document_to_sap_records(
        self,
        raw_document_text: str,
        preferred_entity: Optional[str] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Intelligently transforms raw document text/tables into structured SAP Business One master data records using Nemotron.
        """
        import json
        import re

        system_prompt = """
You are an expert SAP ERP Data Integration Engineer.
Your task is to analyze the provided raw document content (from PDF or Excel) and extract/convert it into structured SAP Master Data records.

Target Entity Types & Schemas:
1. "business_partner":
   - CardCode: string (e.g. C1001, V2002)
   - CardName: string
   - CardType: "cCustomer" (for customers/clients) or "cSupplier" (for vendors/suppliers)
   - FederalTaxID: string (GSTIN, 15 alphanumeric if in India)
   - Phone1: string
   - EmailAddress: string
   - Address: string
   - City: string
   - State: string (2-letter state code e.g. MH, DL, KA)
   - ZipCode: string
   - Country: "IN"

2. "item":
   - ItemCode: string (e.g. ITM-001)
   - ItemName: string
   - ItemsGroupCode: integer (e.g. 100)
   - SalesUnit: string (e.g. NOS, KG)
   - PurchaseUnit: string (e.g. NOS, KG)
   - QuantityOnStock: float/number
   - TaxCodeAR: string (e.g. GST_18)
   - ChapterID: integer or HSN code

3. "warehouse":
   - WarehouseCode: string (e.g. WH01)
   - WarehouseName: string
   - Street: string
   - City: string
   - State: string
   - Country: "IN"

OUTPUT REQUIREMENTS:
Respond ONLY with a valid JSON object in the following format. Do NOT include any markdown code blocks, backticks, or explanatory text:
{
  "master_type": "business_partner" | "item" | "warehouse",
  "records": [
     { ... fields ... }
  ],
  "confidence": 0.95,
  "summary": "Extracted N records of type X"
}
"""
        pref_str = f"Preferred Entity Type: {preferred_entity}\n\n" if preferred_entity else ""
        instr_str = f"Specific User Instructions / Mapping Rules: {custom_instructions}\n\n" if custom_instructions else ""
        user_prompt = f"{pref_str}{instr_str}Raw Document Content to Transform:\n{raw_document_text[:8000]}"

        response_text = await self.generate(system_prompt=system_prompt, user_prompt=user_prompt)

        try:
            # Strip backticks and json tag if present
            cleaned = re.sub(r"^```(?:json)?", "", response_text.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            
            # Extract JSON substring if surrounded by extra text
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1:
                cleaned = cleaned[start_idx:end_idx + 1]
            
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "records" in parsed and isinstance(parsed["records"], list):
                return parsed
        except Exception as e:
            logger.warning(f"Failed to parse LLM structured document output: {e}. Raw was: {response_text[:200]}")

        # Fallback return
        return {
            "master_type": preferred_entity or "business_partner",
            "records": [],
            "confidence": 0.0,
            "summary": "AI extraction yielded no parsable records."
        }

nvidia_chat_service = NVIDIAChatService()
