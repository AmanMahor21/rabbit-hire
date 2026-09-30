# backend/app/services/skill_normalizer.py
from __future__ import annotations
import hashlib
from typing import List
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
from app.core.qdrant import get_qdrant_client, get_embedding_model

TAXONOMY_COLLECTION = getattr(
    settings, "SKILL_TAXONOMY_COLLECTION", "skill_taxonomy")
THRESHOLD = getattr(settings, "SKILL_SIMILARITY_THRESHOLD", 0.85)


def ensure_taxonomy_collection():
    client = get_qdrant_client()
    existing = {c.name for c in client.get_collections().collections}
    if TAXONOMY_COLLECTION not in existing:
        client.create_collection(
            collection_name=TAXONOMY_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )


def _skill_id(skill: str) -> str:
    return hashlib.md5(skill.lower().encode("utf-8")).hexdigest()


def normalize_skills(skills: List[str]) -> List[str]:
    if not skills:
        return []
    ensure_taxonomy_collection()
    client = get_qdrant_client()
    model = get_embedding_model()
    canonical = []
    points_to_upsert = []

    for raw in skills:
        if not raw or len(raw.strip()) < 2:
            continue
        raw_clean = raw.strip()
        vec = model.encode([raw_clean], normalize_embeddings=True)[0].tolist()
        hits = client.query_points(
            collection_name=TAXONOMY_COLLECTION,
            query=vec,
            limit=1,
            with_payload=True
        ).points

        if hits and hits[0].score >= THRESHOLD:
            canonical.append(hits[0].payload["canonical"])
        else:
            can = raw_clean.upper()
            canonical.append(can)
            points_to_upsert.append(
                PointStruct(
                    id=_skill_id(can),
                    vector=vec,
                    payload={"canonical": can, "variants": [raw_clean]}
                )
            )

    if points_to_upsert:
        client.upsert(collection_name=TAXONOMY_COLLECTION,
                      points=points_to_upsert, wait=True)

    seen = set()
    out = []
    for c in canonical:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out
