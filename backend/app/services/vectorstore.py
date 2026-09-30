# backend/app/services/vectorstore.py - PRODUCTION SAAS
from __future__ import annotations
import hashlib
from typing import Any, List, Dict
import numpy as np
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchAny,
    Range
)
from app.core.config import settings
from app.core.qdrant import get_qdrant_client, get_embedding_model
from app.services.rag import rerank_and_boost

COLLECTION_NAME = getattr(settings, "QDRANT_COLLECTION", "resume_profiles")
VECTOR_SIZE = 384

# Singleton clients - avoid file lock
client = get_qdrant_client()
embedding_model = get_embedding_model()


def ensure_collection() -> None:
    q_client = get_qdrant_client()
    existing = {c.name for c in q_client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[VECTORSTORE] Created collection {COLLECTION_NAME}")


def profile_id(filename: str) -> str:
    return hashlib.md5(filename.encode("utf-8")).hexdigest()


def create_embedding(text: str, skills: List[str] | None = None) -> List[float]:
    """Enriched embedding for better location + skill search"""
    skills = skills or []
    model = get_embedding_model()
    # Important: include skills + location in embedding text for better recall
    enriched = f"Skills: {', '.join(skills[:80])}\n\nResume:\n{text[:3000]}"
    vector = model.encode([enriched], normalize_embeddings=True)[0]
    return np.asarray(vector, dtype=np.float32).tolist()


def upsert_profiles(df) -> int:
    if df is None or df.empty:
        return 0
    ensure_collection()
    q_client = get_qdrant_client()
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
            "domains": _as_list(row.get("domains", [])),
            "education": _as_list(row.get("education", [])),
            "text": text[:10000],
        }

        points.append(PointStruct(
            id=profile_id(filename),
            vector=create_embedding(text, skills + skills_raw),
            payload=payload
        ))

    if not points:
        return 0

    q_client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
    print(f"[VECTORSTORE] Upserted {len(points)} points")
    return len(points)


def _build_qdrant_filter(filters: Dict[str, Any] | None) -> Filter | None:
    """Production SaaS filter - uses Qdrant native filtering, not python contains"""
    if not filters:
        return None

    must_conditions = []

    # Location filter - payload location is array e.g. ["Delhi", "Noida"]
    req_locs = filters.get("locations") or filters.get("location") or []
    if req_locs:
        # Normalize to Title case for Qdrant MatchAny
        locs_normalized = [str(l).strip() for l in req_locs if str(l).strip()]
        if locs_normalized:
            must_conditions.append(
                FieldCondition(
                    key="location", match=MatchAny(any=locs_normalized))
            )

    # Experience filter - min experience
    min_exp = filters.get("experience")
    if min_exp:
        try:
            must_conditions.append(
                FieldCondition(key="experience", range=Range(gte=int(min_exp)))
            )
        except:
            pass

    # Skills - we DON'T filter skills via Qdrant for recall, we let vector + reranker handle it
    # If you want strict skill filtering, uncomment:
    # req_skills = filters.get("skills") or []
    # if req_skills:
    # must_conditions.append(FieldCondition(key="skills", match=MatchAny(any=req_skills)))

    if not must_conditions:
        return None

    return Filter(must=must_conditions)


# backend/app/services/vectorstore.py

def _matches_filters_python(payload: Dict[str, Any], filters: Dict[str, Any] | None) -> bool:
    """Hard constraints. required_skills use AND semantics."""
    if not filters:
        return True

    # ----- Location (must match at least one) -----
    req_locs = filters.get("locations") or filters.get("location") or []
    if req_locs:
        combined = (
            " ".join(str(x) for x in (payload.get("location") or [])) + " " +
            (payload.get("text") or "")
        ).lower()
        if not any(str(l).lower() in combined for l in req_locs):
            return False

    # ----- Experience -----
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

    # ----- REQUIRED SKILLS – every one must be present (AND) -----
    required = [str(s).strip().lower()
                for s in (filters.get("skills") or []) if s]
    if required:
        haystack = (
            (payload.get("text") or "") + " " +
            " ".join(str(s) for s in (payload.get("skills") or [])) + " " +
            " ".join(str(s) for s in (payload.get("skills_raw") or []))
        ).lower()
        for skill in required:
            if skill not in haystack:
                return False          # reject immediately

    return True


def filter_only_search(
    filters: Dict[str, Any] | None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    Browse the corpus using ONLY payload filters — no vector similarity.
    Used when the user sends filters but no query text.
    """
    ensure_collection()
    q_client = get_qdrant_client()          # ← creates its own client

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
        return []

    scored: List[Dict[str, Any]] = []
    for p in records:
        payload = p.payload or {}
        if not _matches_filters_python(payload, filters):
            continue
        scored.append({
            "id": str(p.id),
            "score": 0.5,
            "payload": payload,
        })

    scored.sort(
        key=lambda d: int(d["payload"].get("experience") or 0),
        reverse=True,
    )
    print(f"[FILTER_ONLY_SEARCH] filters={filters} → {len(scored)} results")
    return scored[:top_k]


def hybrid_search(query: str, top_k: int = 10, filters: Dict[str, Any] | None = None, min_score: float = 0.0) -> List[Dict[str, Any]]:
    """
    Production hybrid search:
    1. Qdrant vector search with native filter
    2. Python fallback filter for fuzzy matching
    3. Cross-encoder rerank
    """
    ensure_collection()
    query = query.strip()
    # if not query:
    #     return []

    q_client = get_qdrant_client()

    # Candidate pool - 5x top_k for reranking
    candidate_limit = min(max(top_k * 5, 50), 100)
    q_vec = create_embedding(query, [])

    # Build Qdrant native filter for location/experience
    qdrant_filter = _build_qdrant_filter(filters)

    print(
        f"[HYBRID_SEARCH] query='{query[:80]}' filters={filters} qdrant_filter={qdrant_filter} top_k={top_k}")

    try:
        resp = q_client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            query_filter=qdrant_filter,
            limit=candidate_limit,
            with_payload=True
        )
    except Exception as e:
        print(
            f"[HYBRID_SEARCH] Qdrant query failed: {e}, retrying without filter")
        resp = q_client.query_points(
            collection_name=COLLECTION_NAME,
            query=q_vec,
            limit=candidate_limit,
            with_payload=True
        )

    scored = []
    for p in resp.points:
        # Extra python filtering for skills (more recall than strict Qdrant filter)
        if not _matches_filters_python(p.payload or {}, filters):
            continue
        if p.score < min_score:
            continue
        scored.append({
            "id": str(p.id),
            "score": float(p.score),
            "payload": p.payload or {}
        })

    if not scored:
        print(f"[HYBRID_SEARCH] 0 results after filtering")
        return []

    # Rerank with cross-encoder
    reranked = rerank_and_boost(query=query, docs=scored, top_k=top_k)
    print(f"[HYBRID_SEARCH] returning {len(reranked)} docs")
    return reranked[:top_k]


def clear_collection() -> None:
    q_client = get_qdrant_client()
    try:
        q_client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"[VECTORSTORE] Deleted collection {COLLECTION_NAME}")
    except Exception as e:
        print(f"[VECTORSTORE] Delete failed: {e}")
    ensure_collection()
