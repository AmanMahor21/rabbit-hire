# backend/app/tasks/ingest_tasks.py
import asyncio
from app.core.celery_app import celery
from app.services.ingestion import ingest_all
from app.services.vectorstore import upsert_profiles
from app.api.routes_filters import invalidate_filter_cache


@celery.task(name="process_resumes")
def process_resumes_task():
    df = ingest_all()
    if df.empty:
        return {"message": "No valid resumes found", "count": 0}

    count = upsert_profiles(df)

    # ✅ Invalidate the filter cache — next GET /api/filters will recompute
    try:
        asyncio.run(invalidate_filter_cache())
    except Exception as exc:
        print(f"[ingest] filter cache invalidation failed: {exc}")

    return {
        "message": f"Indexed {len(df)} resumes ({count} vectors)",
        "count": len(df),
    }
