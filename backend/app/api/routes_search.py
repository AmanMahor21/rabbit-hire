# backend/app/api/routes_search.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
import pandas as pd
from ..models import SearchRequest
from ..services.vectorstore import hybrid_search, filter_only_search

router = APIRouter()
_EXPERIENCE_BUCKETS = ["0-2", "3-5", "6-10", "10+"]


def _bucket_experience(years: int) -> str:
    if years <= 2:
        return "0-2"
    if years <= 5:
        return "3-5"
    if years <= 10:
        return "6-10"
    return "10+"


def _has_active_filters(filters) -> bool:
    """True if any filter field carries a value."""
    if filters is None:
        return False
    return bool(
        (filters.skills or [])
        or (filters.locations or [])
        or (filters.domains or [])
        or (filters.degrees or [])
        or (filters.experience or 0) > 0
    )


@router.post("/search")
async def search(req: SearchRequest):
    query = (req.query or "").strip()
    filters_payload = req.filters.model_dump() if req.filters else None
    has_filters = _has_active_filters(req.filters)

    # ─────────────────────────────────────────────────────────────
    # Case 1: nothing to search with
    # ─────────────────────────────────────────────────────────────
    if not query and not has_filters:
        return {
            "results": [],
            "charts": {},
            "parsed_filters": req.filters.dict() if req.filters else {},
            "rewritten_query": "",
        }

    # ─────────────────────────────────────────────────────────────
    # Case 2: filters only → browse mode
    # ─────────────────────────────────────────────────────────────
    if not query:
        results = filter_only_search(
            filters=filters_payload,
            top_k=req.top_k,
        )
        rewritten = ""   # nothing was rewritten

    # ─────────────────────────────────────────────────────────────
    # Case 3: query present (with or without filters) → hybrid search
    # ─────────────────────────────────────────────────────────────
    else:
        results = hybrid_search(
            query=query,
            top_k=req.top_k,
            filters=filters_payload,
        )
        rewritten = query

    # ─────────────────────────────────────────────────────────────
    # Shape the response (identical to before)
    # ─────────────────────────────────────────────────────────────
    candidates = []
    for r in results:
        p = r["payload"]
        candidates.append({
            "filename": p.get("filename", ""),
            "skills": p.get("skills", []),
            "skills_raw": p.get("skills_raw", []),
            "location": p.get("location", []),
            "experience_years": int(p.get("experience", 0) or 0),
            "domains": p.get("domains", []),
            "text": p.get("text", ""),
            "evidence": p.get("text", "")[:200],
            "email": p.get("email"),
            "score": r.get("rerank_score", r.get("score", 0)),
        })

    charts = {}
    if candidates:
        df = pd.DataFrame(candidates)
        top_skills = (
            pd.Series([s for sl in df["skills"] for s in sl])
            .value_counts()
            .head(10)
        )
        bucket_counts = {b: 0 for b in _EXPERIENCE_BUCKETS}
        for years in df["experience_years"]:
            bucket_counts[_bucket_experience(int(years))] += 1
        charts = {
            "top_skills": {
                "labels": top_skills.index.tolist(),
                "data": top_skills.values.tolist(),
            },
            "experience_dist": {
                "labels": _EXPERIENCE_BUCKETS,
                "data": [bucket_counts[b] for b in _EXPERIENCE_BUCKETS],
            },
        }

    return {
        "results": candidates,
        "charts": charts,
        "parsed_filters": req.filters.dict() if req.filters else {},
        "rewritten_query": rewritten,
    }
