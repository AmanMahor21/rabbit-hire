# backend/app/core/qdrant.py
from __future__ import annotations
import os
from app.core.config import settings

_qdrant_client = None
_embedding_model = None


def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    from qdrant_client import QdrantClient
    # Production: set QDRANT_URL env to use server and avoid file lock completely
    qdrant_url = getattr(settings, "QDRANT_URL", None)
    if qdrant_url:
        _qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=os.getenv("QDRANT_API_KEY") or getattr(
                settings, "QDRANT_API_KEY", None),
        )
    else:
        path = getattr(settings, "QDRANT_PATH", "./qdrant_data")
        os.makedirs(path, exist_ok=True)
        _qdrant_client = QdrantClient(path=path)
    return _qdrant_client


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model
