# backend/app/services/vectorstore.py
from __future__ import annotations

import hashlib
import math
import time
from typing import Any, Dict, List

import numpy as np
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchAny,
    PointStruct,
    Range,
    VectorParams,
)

from app.core.config import settings
from app.core.metrics import (
    SEARCH_EMPTY,
    SEARCH_LATENCY,
    SEARCH_REQUESTS,
)
from app.core.qdrant import get_embedding_model, get_qdrant_client, get_embedding_dimension
from app.services.location_normalize import (
    expand_for_filter,
    locations_match,
    normalize_locations,
)
from app.services.rag import rerank_and_boost

COLLECTION_NAME = getattr(settings, "QDRANT_COLLECTION", "resume_profiles")


def get_client():
    """Return the Qdrant client (cached inside core.qdrant)."""
    return get_qdrant_client()


def get_model():
    """Return the sentence-transformer embedding model (cached inside core.qdrant)."""
    return get_embedding_model()


def ensure_collection() -> None:
    q_client = get_client()
    existing = {c.name for c in q_client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=get_embedding_dimension(), distance=Distance.COSINE),
        )


def profile_id(filename: str) -> str:
    # Qdrant point IDs must be an unsigned integer or a UUID (32 hex chars).
    # sha256 gives 64 hex chars, which Qdrant rejects with HTTP 400, so we
    # take the first 32 hex chars -> a valid UUID-form ID.
    digest = hashlib.sha256(
        filename.strip().lower().encode("utf-8")).hexdigest()
    return digest[:32]


def create_embedding(text: str, skills: List[str] | None = None) -> List[float]:
    skills = skills or []
    model = get_model()
    enriched = f"Skills: {', '.join(skills[:80])}\n\nResume:\n{text[:3000]}"
    vector = model.encode([enriched], normalize_embeddings=True)[0]
    return np.asarray(vector, dtype=np.float32).tolist()


def _clean_payload(value):
    """Recursively replace non-finite floats (NaN/inf) with None.

    pandas converts missing Python None values into np.nan, which Qdrant
    rejects (HTTP 400) because NaN is not valid JSON. This normalizes them
    so every payload is JSON-safe.
    """
    if isinstance(value, float):
        return None if (math.isnan(value) or math.isinf(value)) else value
    if isinstance(value, list):
        return [_clean_payload(v) for v in value]
    if isinstance(value, dict):
        return {k: _clean_payload(v) for k, v in value.items()}
    return value


def upsert_profiles(df) -> int:
    if df is None or df.empty:
        return 0
    ensure_collection()
    q_client = get_client()
    points: List[PointStruct] = []

    for _, row in df.iterrows():
        filename = str(row.get("filename", ""))
        if not filename:
            continue
        text = str(row.get("text", ""))
        skills = row.get("skills", []) or []
        skills_raw = row.get("skills_raw", []) or []

        def _as_list(v):
            return v if isinstance(v, list) else [v] if v else []

        payload = {
            "filename": filename,
            "file_hash": str(row.get("file_hash", "")),
            "name": str(row.get("name", filename)),
            "email": row.get("email"),
            "phone": row.get("phone"),
            "skills": _as_list(skills),
            "skills_raw": _as_list(skills_raw),
            "experience": int(row.get("experience", 0) or 0),
            "location": _as_list(row.get("location", [])),
            "location_canonical": _as_list(row.get("location_canonical", [])),
            "domains": _as_list(row.get("domains", [])),
            "education": _as_list(row.get("education", [])),
            "text": text[:10000],
            "summary": str(row.get("summary", "") or "")[:2000],
        }

        points.append(
            PointStruct(
                id=profile_id(filename),
                vector=create_embedding(text, skills + skills_raw),
                payload=_clean_payload(payload),
            )
        )

    if not points:
        return 0

    q_client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    return len(points)


def _build_qdrant_filter(filters: Dict[str, Any] | None) -> Filter | None:
    if not filters:
        return None

    must_conditions: List[Any] = []
    should_conditions: List[Any] = []

    req_locs = filters.get("locations") or filters.get("location") or []
    if req_locs:
        expanded = expand_for_filter(req_locs)
        canon = normalize_locations(req_locs)
        if expanded:
            should_conditions.append(
                FieldCondition(key="location", match=MatchAny(any=expanded))
            )
        if canon:
            should_conditions.append(
                FieldCondition(
                    key="location_canonical", match=MatchAny(any=canon)
                )
            )

    min_exp = filters.get("experience") or filters.get("min_experience")
    if min_exp:
        try:
            must_conditions.append(
                FieldCondition(key="experience", range=Range(gte=int(min_exp)))
            )
        except (TypeError, ValueError):
            pass

    if not must_conditions and not should_conditions:
        return None

    if should_conditions and must_conditions:
        try:
            from qdrant_client.models import MinShould

            return Filter(
                must=must_conditions,
                min_should=MinShould(
                    conditions=should_conditions, min_count=1
                ),
            )
        except Exception:
            return Filter(must=must_conditions, should=should_conditions)

    if must_conditions:
        return Filter(must=must_conditions)
    return Filter(should=should_conditions)


def _matches_filters_python(
    payload: Dict[str, Any], filters: Dict[str, Any] | None
) -> bool:
    if not filters:
        return True

    req_locs = filters.get("locations") or filters.get("location") or []
    if req_locs:
        if not locations_match(
            payload.get("location") or [],
            payload.get("location_canonical") or [],
            req_locs,
        ):
            return False

    min_exp = filters.get("min_experience") or filters.get("experience")
    if min_exp is not None:
        try:
            if int(payload.get("experience") or 0) < int(min_exp):
                return False
        except (TypeError, ValueError):
            pass

    max_exp = filters.get("max_experience")
    if max_exp is not None:
        try:
            if int(payload.get("experience") or 0) > int(max_exp):
                return False
        except (TypeError, ValueError):
            pass

    required = [
        str(s).strip().lower() for s in (filters.get("skills") or []) if s
    ]
    if required:
        haystack = (
            (payload.get("text") or "")
            + " "
            + " ".join(str(s) for s in (payload.get("skills") or []))
            + " "
            + " ".join(str(s) for s in (payload.get("skills_raw") or []))
        ).lower()
        for skill in required:
            if skill not in haystack:
                return False

    return True


def _filters_present_label(filters: Dict[str, Any] | None) -> str:
    if not filters:
        return "false"
    return "true" if any(bool(v) for v in filters.values()) else "false"


def filter_only_search(
    filters: Dict[str, Any] | None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    start = time.perf_counter()
    SEARCH_REQUESTS.labels(mode="filter_only").inc()
    try:
        ensure_collection()
        q_client = get_qdrant_client()
        qdrant_filter = _build_qdrant_filter(filters)

        try:
            records, _ = q_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=qdrant_filter,
                limit=min(max(top_k * 5, 100), 500),
                with_payload=True,
                with_vectors=False,
            )
        except Exception as e:
            print(f"[FILTER_ONLY_SEARCH] scroll failed: {e}")
            SEARCH_EMPTY.labels(
                filters_present=_filters_present_label(filters)).inc()
            return []

        scored: List[Dict[str, Any]] = []
        for p in records:
            payload = p.payload or {}
            if not _matches_filters_python(payload, filters):
                continue
            scored.append({"id": str(p.id), "score": 0.5, "payload": payload})

        scored.sort(
            key=lambda d: int(d["payload"].get("experience") or 0),
            reverse=True,
        )

        if not scored:
            SEARCH_EMPTY.labels(
                filters_present=_filters_present_label(filters)
            ).inc()

        return scored[:top_k]
    finally:
        SEARCH_LATENCY.labels(mode="filter_only").observe(
            time.perf_counter() - start
        )


def hybrid_search(
    query: str,
    top_k: int = 10,
    filters: Dict[str, Any] | None = None,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    start = time.perf_counter()
    SEARCH_REQUESTS.labels(mode="hybrid").inc()
    try:
        ensure_collection()
        query = (query or "").strip()
        q_client = get_qdrant_client()

        candidate_limit = min(max(top_k * 5, 50), 100)
        q_vec = create_embedding(query, [])
        qdrant_filter = _build_qdrant_filter(filters)

        try:
            resp = q_client.query_points(
                collection_name=COLLECTION_NAME,
                query=q_vec,
                query_filter=qdrant_filter,
                limit=candidate_limit,
                with_payload=True,
            )
        except Exception:
            resp = q_client.query_points(
                collection_name=COLLECTION_NAME,
                query=q_vec,
                limit=candidate_limit,
                with_payload=True,
            )

        scored = []
        for p in resp.points:
            if not _matches_filters_python(p.payload or {}, filters):
                continue
            if p.score < min_score:
                continue
            scored.append(
                {
                    "id": str(p.id),
                    "score": float(p.score),
                    "payload": p.payload or {},
                }
            )

        if not scored:
            if filters and (filters.get("locations") or filters.get("location")):
                SEARCH_REQUESTS.labels(mode="soft_retry").inc()
                soft = dict(filters)
                soft.pop("locations", None)
                soft.pop("location", None)
                try:
                    resp2 = q_client.query_points(
                        collection_name=COLLECTION_NAME,
                        query=q_vec,
                        query_filter=_build_qdrant_filter(
                            soft) if soft else None,
                        limit=candidate_limit,
                        with_payload=True,
                    )
                    for p in resp2.points:
                        if not _matches_filters_python(p.payload or {}, filters):
                            continue
                        scored.append(
                            {
                                "id": str(p.id),
                                "score": float(p.score),
                                "payload": p.payload or {},
                            }
                        )
                except Exception:
                    pass

        if not scored:
            SEARCH_EMPTY.labels(
                filters_present=_filters_present_label(filters)
            ).inc()
            return []

        reranked = rerank_and_boost(query=query, docs=scored, top_k=top_k)

        if not reranked:
            SEARCH_EMPTY.labels(
                filters_present=_filters_present_label(filters)
            ).inc()

        return reranked[:top_k]
    finally:
        SEARCH_LATENCY.labels(mode="hybrid").observe(
            time.perf_counter() - start
        )


def clear_collection() -> None:
    q_client = get_qdrant_client()
    try:
        q_client.delete_collection(collection_name=COLLECTION_NAME)
    except Exception:
        pass
    ensure_collection()
