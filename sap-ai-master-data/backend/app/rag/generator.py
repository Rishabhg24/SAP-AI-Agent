"""
RAG Generator combining semantic retrieval, NVIDIA LLM, and citation synthesis.
"""
from typing import Any, Dict, List, Optional
from app.rag.prompts import RAG_ANSWERING_PROMPT, STRICT_SAP_SYSTEM_PROMPT
from app.rag.retriever import retriever
from app.services.chat_service import nvidia_chat_service

class RAGGenerator:
    async def ask(
        self,
        question: str,
        entity: Optional[str] = None,
        top_k: int = 4
    ) -> Dict[str, Any]:
        """
        Execute full RAG generation pipeline:
        1. Handle general conversational greetings immediately
        2. Retrieve top matching chunks from ChromaDB
        3. Build context string
        4. Call NVIDIA LLM with strict SAP system prompt
        5. Assemble citations without fabricating page numbers
        """
        q_clean = question.strip().lower().rstrip("!.?")
        if q_clean in ["hi", "hello", "hey", "good morning", "good afternoon", "greetings", "help", "who are you", "what can you do"]:
            return {
                "answer": (
                    "Hello! I am your SAP AI Assistant.\n\n"
                    "I can assist you with:\n"
                    "• **Master Data Extraction**: Upload PDF, Excel, or CSV documents for Items, Suppliers/Customers, and Warehouses.\n"
                    "• **Deterministic Validation**: Verify mandatory fields, types, and business rules before posting.\n"
                    "• **Missing Field Resolution**: Guide you through entering missing mandatory fields.\n"
                    "• **SAP Knowledge Base**: Answer technical questions regarding SAP Service Layer entities and API schemas.\n\n"
                    "How can I help you today?"
                ),
                "sources": []
            }

        k = min(top_k or 4, 4)
        search_results = retriever.search(question, top_k=k, entity=entity)
        
        if not search_results:
            return {
                "answer": "The SAP documentation available to me is insufficient to answer your question.",
                "sources": []
            }

        # Build context
        context_parts = []
        sources = []
        seen_sources = set()

        for idx, res in enumerate(search_results, 1):
            source_doc = res.get("source", "SAP Documentation")
            section = res.get("metadata", {}).get("section", "General")
            source_key = f"{source_doc}::{section}"
            
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                src_info: Dict[str, Any] = {
                    "document": source_doc,
                    "section": section,
                    "score": res.get("score")
                }
                # Include page if explicitly present in metadata, never fabricate
                if "page" in res.get("metadata", {}) and res["metadata"]["page"]:
                    src_info["page"] = res["metadata"]["page"]
                sources.append(src_info)

            context_parts.append(
                f"[Source {idx}: {source_doc} - Section: {section}]\n{res['content']}"
            )

        context_str = "\n\n".join(context_parts)
        user_prompt = RAG_ANSWERING_PROMPT.format(context=context_str, question=question)

        answer = await nvidia_chat_service.generate(
            system_prompt=STRICT_SAP_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            context=""
        )

        return {
            "answer": answer.strip(),
            "sources": sources
        }

rag_generator = RAGGenerator()
