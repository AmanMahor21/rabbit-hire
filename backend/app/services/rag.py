# backend/app/services/rag.py
from __future__ import annotations
import re
from typing import Any
from sentence_transformers import CrossEncoder
from app.core.config import settings

try:
    reranker = CrossEncoder(settings.RERANK_MODEL)
except Exception as exc:
    print(f"CrossEncoder load failed: {exc}")
    reranker = None

RERANK_RELATIVE_MARGIN = 2.5
RERANK_ABSOLUTE_FLOOR = -3.0


def _boost_score(doc: dict[str, Any], query: str) -> int:
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

    boosted = []
    for doc in docs:
        boosted.append({**doc, "boost": _boost_score(doc, query)})

    boosted.sort(key=lambda d: (d["boost"], d["score"]), reverse=True)

    if reranker is None:
        return boosted[:top_k]

    RERANK_POOL_SIZE = 40
    pool = boosted[:RERANK_POOL_SIZE]

    pairs = [[query, doc["payload"].get("text", "")[:800]] for doc in pool]

    try:
        raw_scores = reranker.predict(pairs)
    except Exception as exc:
        print(f"Rerank error: {exc}")
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
