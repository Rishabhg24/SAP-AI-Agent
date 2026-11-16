"""
Unit tests for RAG retrieval and citations.
"""
from app.rag.retriever import retriever

def test_rag_warehouse_search():
    results = retriever.search("What fields are required for creating a warehouse?", top_k=3)
    assert len(results) > 0
    first_result = results[0]
    assert "WarehouseCode" in first_result["content"] or "warehouse" in first_result["content"].lower()
    assert first_result["source"] is not None
    assert first_result["metadata"]["section"] is not None
    assert first_result["score"] > 0.0

def test_rag_item_search():
    results = retriever.search("What are the mandatory fields for Item Master?", top_k=3)
    assert len(results) > 0
    assert any("ItemCode" in r["content"] for r in results)
