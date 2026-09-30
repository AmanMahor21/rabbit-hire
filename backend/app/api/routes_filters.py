# backend/app/api/routes_filters.py
from __future__ import annotations

from collections import Counter
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List

from app.services.vectorstore import client, COLLECTION_NAME
from app.core.redis_client import get_redis
import json

router = APIRouter(tags=["Filters"])

CACHE_KEY = "talent:filters:v2"  # bumped version — shape changed
CACHE_TTL_SECONDS = 300


class FilterOptions(BaseModel):
    skills: List[str]
    locations: List[str]
    domains: List[str]
    degrees: List[str]
    experience_range: dict
    # counts so the UI can show "React (42)"
    skill_counts: Dict[str, int]
    location_counts: Dict[str, int]
    domain_counts: Dict[str, int]


DEGREES = ["B.Tech", "M.Tech", "Bachelor", "Master", "PhD", "Diploma"]
EXPERIENCE_MAX = 30


def _derive_filters_from_qdrant() -> FilterOptions:
    try:
        records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=["skills", "location", "domains", "experience"],
            with_vectors=False,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Corpus unavailable: {exc}")

    skill_counter: Counter[str] = Counter()
    loc_counter: Counter[str] = Counter()
    domain_counter: Counter[str] = Counter()
    max_exp = 0

    for r in records:
        p = r.payload or {}
        for s in (p.get("skills") or []):
            if s and isinstance(s, str) and s.strip():
                skill_counter[s.strip()] += 1
        for l in (p.get("location") or []):
            if l and isinstance(l, str) and l.strip():
                loc_counter[l.strip()] += 1
        for d in (p.get("domains") or []):
            if d and isinstance(d, str) and d.strip():
                domain_counter[d.strip()] += 1
        try:
            max_exp = max(max_exp, int(p.get("experience") or 0))
        except (TypeError, ValueError):
            pass

    # Sort by count desc, then alphabetical — so the first 15 are genuinely the popular ones
    skills_sorted = [s for s, _ in skill_counter.most_common()]
    locs_sorted = [l for l, _ in loc_counter.most_common()]
    domains_sorted = [d for d, _ in domain_counter.most_common()]

    return FilterOptions(
        skills=skills_sorted,
        locations=locs_sorted,
        domains=domains_sorted,
        degrees=DEGREES,
        experience_range={"min": 0, "max": min(max_exp + 2, EXPERIENCE_MAX)},
        skill_counts=dict(skill_counter),
        location_counts=dict(loc_counter),
        domain_counts=dict(domain_counter),
    )


@router.get("/filters", response_model=FilterOptions)
async def get_filters():
    redis = get_redis()
    try:
        cached = await redis.get(CACHE_KEY)
        if cached:
            return FilterOptions(**json.loads(cached))
    except Exception:
        pass

    filters = _derive_filters_from_qdrant()

    try:
        await redis.setex(CACHE_KEY, CACHE_TTL_SECONDS, filters.model_dump_json())
    except Exception:
        pass

    return filters


async def invalidate_filter_cache() -> None:
    redis = get_redis()
    try:
        await redis.delete(CACHE_KEY)
    except Exception:
        pass
