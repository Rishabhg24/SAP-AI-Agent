"""
Embedding provider for SAP Knowledge Base.
Uses ChromaDB's ONNX all-MiniLM-L6-v2 implementation locally.
Works 100% offline without requiring external API keys.
"""
from typing import List
import chromadb.utils.embedding_functions as ef
from app.config import settings
from app.utils.logging import logger

class SAPEmbeddingProvider:
    def __init__(self):
        # Local ONNX all-MiniLM-L6-v2 embedding function
        self._ef = ef.DefaultEmbeddingFunction()
        logger.info(f"Initialized local embedding function: {settings.embedding_model}")

    def get_embedding_function(self):
        return self._ef

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._ef(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._ef([text])[0]

embedding_provider = SAPEmbeddingProvider()
