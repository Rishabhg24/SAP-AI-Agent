"""
RAG Retriever for querying SAP Knowledge Base in ChromaDB.
Supports semantic search, similarity score calculation, and metadata filtering.
"""
from typing import Any, Dict, List, Optional
import chromadb
from app.config import settings
from app.rag.embeddings import embedding_provider
from app.utils.logging import logger

class SAPRetriever:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.rag_db_path)
        self._collection = self._client.get_or_create_collection(
            name=settings.rag_collection_name,
            embedding_function=embedding_provider.get_embedding_function()
        )

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        entity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the SAP documentation collection.
        Returns top matching chunks with scores and metadata.
        """
        k = top_k or settings.rag_top_k
        where_clause = None
        if entity and entity.lower() != "all":
            # Map entity to stored format
            entity_norm = entity.title().replace(" ", "").replace("_", "")
            where_clause = {"entity": entity_norm}

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause
            )
        except Exception as e:
            logger.warning(f"Filtered query failed ({e}), falling back to unfiltered search.")
            results = self._collection.query(
                query_texts=[query],
                n_results=k
            )

        formatted_results = []
        if not results or not results.get("documents"):
            return formatted_results

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.5] * len(docs)

        for doc, meta, dist in zip(docs, metas, distances):
            # Chroma returns L2 distance; convert to approximate cosine/similarity score [0, 1]
            similarity_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))
            formatted_results.append({
                "content": doc,
                "source": meta.get("source", "SAP Documentation"),
                "score": round(similarity_score, 4),
                "metadata": {
                    "entity": meta.get("entity", "General"),
                    "document_type": meta.get("document_type", "Reference"),
                    "section": meta.get("section", "General"),
                    "file_path": meta.get("file_path", "")
                }
            })

        return formatted_results

retriever = SAPRetriever()
