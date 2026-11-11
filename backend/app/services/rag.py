# backend/app/services/rag.py
from __future__ import annotations
import re
from typing import Any, Optional

# NOTE: We do NOT import CrossEncoder at the top of the file.
# If we did, every reload would re-download/reload the reranker.
# Instead we load it lazily the first time rerank_and_boost() is called.
from app.core.config import settings
from app.core.metrics import RERANK_FALLBACKS

RERANK_RELATIVE_MARGIN = 2.5
RERANK_ABSOLUTE_FLOOR = -3.0

# Module-level cache for the reranker model (None = not loaded yet).
# This is the FAANG pattern: lazy singleton.
_reranker = None
_reranker_failed = False   # so we don't retry loading on every request if it broke


def get_reranker():
    """Load the cross-encoder reranker exactly once, on first use."""
    global _reranker, _reranker_failed

    # If we already tried and it failed, don't hammer the disk again.
    if _reranker_failed:
        return None

    # If already loaded, reuse it.
    if _reranker is not None:
        return _reranker

    try:
        # Import inside the function so it only happens on first call.
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(settings.RERANK_MODEL)
        print(f"[RAG] Loaded reranker: {settings.RERANK_MODEL}")
    except Exception as exc:
        print(f"[RAG] CrossEncoder load failed: {exc}")
        _reranker_failed = True
        _reranker = None

    return _reranker


def _boost_score(doc: dict[str, Any], query: str) -> int:
    """Cheap keyword boost — runs before the expensive cross-encoder."""
    payload = doc.get("payload", {})
    haystack = (
        str(payload.get("text", "")) + " " +
        " ".join(payload.get("skills", [])) + " " +
        " ".join(payload.get("skills_raw", [])) + " " +
        " ".join(payload.get("location", []))
    ).lower()
    q_lower = query.lower()
    score = 0
    for token in set(re.findall(r"\b\w{3,}\b", q_lower)):
        if token in haystack:
            score += 10
    return score


def rerank_and_boost(query: str, docs: list[dict[str, Any]], top_k: int = 20) -> list[dict[str, Any]]:
    if not docs:
        return []

    # Step 1: fast keyword boost for all docs.
    boosted = [{**doc, "boost": _boost_score(doc, query)} for doc in docs]
    boosted.sort(key=lambda d: (d["boost"], d["score"]), reverse=True)

    # Step 2: if reranker can't load, return boosted results as-is.
    reranker = get_reranker()
    if reranker is None:
        RERANK_FALLBACKS.inc()
        return boosted[:top_k]

    RERANK_POOL_SIZE = 40
    pool = boosted[:RERANK_POOL_SIZE]

    pairs = [[query, doc["payload"].get("text", "")[:800]] for doc in pool]

    try:
        raw_scores = reranker.predict(pairs)
    except Exception as exc:
        print(f"[RAG] Rerank error: {exc}")
        RERANK_FALLBACKS.inc()
        return boosted[:top_k]

    for doc, score in zip(pool, raw_scores):
        doc["rerank_score"] = float(score)

    pool.sort(key=lambda d: d["rerank_score"], reverse=True)
    if not pool:
        return []

    top_score = pool[0]["rerank_score"]
    dynamic_floor = max(RERANK_ABSOLUTE_FLOOR,
                        top_score - RERANK_RELATIVE_MARGIN)
    relevant = [d for d in pool if d["rerank_score"] >= dynamic_floor]

    return relevant[:top_k]


def generate_evidence(text: str, query: str) -> str:
    q_terms = [t for t in re.findall(
        r"\b\w+\b", query.lower()) if len(t) > 3][:3]
    lower = text.lower()
    for term in q_terms:
        idx = lower.find(term)
        if idx != -1:
            return text[max(0, idx - 80): idx + 200] + "..."
    return text[:200] + "..."
