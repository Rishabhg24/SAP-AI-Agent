"""
RAG Test Command.
Run: python -m app.rag.test
Tests semantic retrieval for query: "What fields are required for creating a warehouse?"
"""
import sys
from app.rag.retriever import retriever

def test_rag():
    test_query = "What fields are required for creating a warehouse?"
    print("==================================================")
    print("SAP RAG RETRIEVAL TEST")
    print("==================================================")
    print(f"Query: '{test_query}'")
    print("Searching ChromaDB collection...")
    
    results = retriever.search(test_query, top_k=3)
    
    if not results:
        print("No documents retrieved! Please run `python -m app.rag.ingest` first.")
        sys.exit(1)
        
    print(f"Found {len(results)} relevant SAP document chunks:")
    for idx, r in enumerate(results, 1):
        print(f"\n--- Result #{idx} (Score: {r['score']}) ---")
        print(f"Source:   {r['source']}")
        print(f"Section:  {r['metadata'].get('section')}")
        print(f"Entity:   {r['metadata'].get('entity')}")
        print("Content Snippet:")
        lines = r['content'].strip().split("\n")[:6]
        for line in lines:
            print(f"  {line}")
            
    print("\n==================================================")
    print("RAG Retrieval Test: PASSED")
    print("==================================================")

if __name__ == "__main__":
    test_rag()
