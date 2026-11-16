"""
RAG API endpoints for semantic search and grounded question answering with citations.
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.rag.generator import rag_generator
from app.rag.retriever import retriever

router = APIRouter(prefix="/api/rag", tags=["RAG Knowledge Base"])

class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    entity: Optional[str] = None

class RAGAskRequest(BaseModel):
    question: str
    entity: Optional[str] = None
    top_k: Optional[int] = 5

@router.post("/search")
async def search_knowledge_base(payload: RAGSearchRequest):
    """Semantic vector search across SAP documentation."""
    results = retriever.search(
        query=payload.query,
        top_k=payload.top_k,
        entity=payload.entity
    )
    return {
        "success": True,
        "status": "SUCCESS",
        "message": f"Found {len(results)} relevant SAP document chunks.",
        "data": {
            "results": results
        }
    }

@router.post("/ask")
async def ask_knowledge_base(payload: RAGAskRequest):
    """
    RAG Grounded Q&A:
    Retrieves authoritative SAP documentation, invokes NVIDIA LLM with strict system prompt,
    and returns grounded answer with full source citations.
    """
    rag_result = await rag_generator.ask(
        question=payload.question,
        entity=payload.entity,
        top_k=payload.top_k or 5
    )
    return {
        "success": True,
        "status": "SUCCESS",
        "message": "Answer generated from authoritative SAP documentation.",
        "data": rag_result
    }
