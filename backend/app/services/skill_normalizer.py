# backend/app/services/skill_normalizer.py
from __future__ import annotations
import numpy as np
import hashlib
from typing import List
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
from app.core.qdrant import get_qdrant_client, get_embedding_model, get_embedding_dimension

TAXONOMY_COLLECTION = getattr(
    settings, "SKILL_TAXONOMY_COLLECTION", "skill_taxonomy")
THRESHOLD = getattr(settings, "SKILL_SIMILARITY_THRESHOLD", 0.85)


def ensure_taxonomy_collection():
    client = get_qdrant_client()
    existing = {c.name for c in client.get_collections().collections}
    if TAXONOMY_COLLECTION not in existing:
        client.create_collection(
            collection_name=TAXONOMY_COLLECTION,
            vectors_config=VectorParams(size=get_embedding_dimension(), distance=Distance.COSINE)
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
    seen_this_batch: dict[str, str] = {}

    for raw in skills:
        if not raw or len(raw.strip()) < 2:
            continue
        raw_clean = raw.strip()
        key = raw_clean.lower()

        if key in seen_this_batch:
            canonical.append(seen_this_batch[key])
            continue

        vec = model.encode([raw_clean], normalize_embeddings=True)[0].tolist()
        hits = client.query_points(
            collection_name=TAXONOMY_COLLECTION,
            query=vec,
            limit=1,
            with_payload=True,
            with_vectors=True,   # required for centroid
        ).points

        if hits and hits[0].score >= THRESHOLD:
            existing = hits[0]
            can = existing.payload["canonical"]
            canonical.append(can)
            seen_this_batch[key] = can

            current_variants = list(existing.payload.get("variants", []))
            if raw_clean not in current_variants:
                current_variants.append(raw_clean)

                # ---- centroid update ----
                n_old = int(existing.payload.get("vector_count", 1) or 1)
                old_vec = (
                    np.asarray(existing.vector, dtype=np.float32)
                    if existing.vector is not None
                    else np.asarray(vec, dtype=np.float32)
                )
                new_vec = np.asarray(vec, dtype=np.float32)
                centroid = (old_vec * n_old + new_vec) / (n_old + 1)
                norm = np.linalg.norm(centroid)
                if norm > 0:
                    centroid = centroid / norm

                points_to_upsert.append(
                    PointStruct(
                        id=existing.id,
                        vector=centroid.tolist(),
                        payload={
                            "canonical": can,
                            "variants": current_variants[:50],
                            "vector_count": n_old + 1,
                        },
                    )
                )
        else:
            can = raw_clean.upper()
            canonical.append(can)
            seen_this_batch[key] = can
            points_to_upsert.append(
                PointStruct(
                    id=_skill_id(can),
                    vector=vec,
                    payload={
                        "canonical": can,
                        "variants": [raw_clean],
                        "vector_count": 1,
                    },
                )
            )

    if points_to_upsert:
        client.upsert(
            collection_name=TAXONOMY_COLLECTION,
            points=points_to_upsert,
            wait=True,
        )

    seen = set()
    out = []
    for c in canonical:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out
