# backend/app/api/routes_agents.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import hashlib
import asyncio
import json
import os

from sse_starlette.sse import EventSourceResponse

from app.db import get_db, SessionLocal
from app.models import HireJob, AgenticHireRequest
from app.tasks.hire_tasks import run_hire_graph

router = APIRouter(tags=["agents"])

SSE_POLL_INTERVAL_SECONDS = float(
    os.getenv("SSE_POLL_INTERVAL_SECONDS", "0.75"))
SSE_MAX_DURATION_SECONDS = int(os.getenv("SSE_MAX_DURATION_SECONDS", "900"))
SSE_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


@router.post("/agentic-hire", status_code=202)
async def agentic_hire(req: AgenticHireRequest, db: Session = Depends(get_db)):
    jd_hash = hashlib.sha256(req.job_description.encode()).hexdigest()[:16]
    existing = db.query(HireJob).filter(
        HireJob.jd_hash == jd_hash,
        HireJob.status.in_(["queued", "running"])
    ).first()
    if existing:
        return {"job_id": existing.id, "status": existing.status, "deduplicated": True}

    safe_top_k = max(1, min(int(req.top_k or 8), 20))

    job = HireJob(
        jd_hash=jd_hash,
        payload={
            "job_description": req.job_description,
            "top_k": safe_top_k,
            "auto_generate_outreach": req.auto_generate_outreach
        },
        status="queued",
        stage="queued",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_hire_graph.delay(job.id)
    return {"job_id": job.id, "status": "queued"}


@router.get("/agentic-hire/{job_id}")
async def get_hire_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(HireJob).filter(HireJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
    }


@router.get("/agentic-hire/{job_id}/stream")
async def stream_hire_status(
    job_id: str,
    request: Request,
):
    # Verify job existence
    with SessionLocal() as db_probe:
        exists = db_probe.query(HireJob.id).filter(
            HireJob.id == job_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        last_signature: str | None = None
        elapsed = 0.0

        try:
            while True:
                # Client disconnected?
                if await request.is_disconnected():
                    break

                # ✅ Fresh scoped session on every tick: guarantees fresh data, NO identity-map caching
                with SessionLocal() as db:
                    job = db.query(HireJob).filter(
                        HireJob.id == job_id).first()
                    if not job:
                        yield {
                            "event": "error",
                            "data": json.dumps({"error": "Job not found"}),
                        }
                        break

                    status = job.status
                    stage = job.stage
                    progress = job.progress
                    result = job.result
                    error = job.error

                payload = {
                    "job_id": job_id,
                    "status": status,
                    "stage": stage,
                    "progress": progress,
                    "result": result if status in SSE_TERMINAL_STATUSES else None,
                    "error": error,
                }

                # Only emit over SSE when progress/stage/status actually changes
                signature = f"{status}|{stage}|{progress}|{bool(result)}"
                if signature != last_signature:
                    last_signature = signature
                    yield {
                        "event": "status",
                        "id": f"{job_id}:{progress}",
                        "data": json.dumps(payload, default=str),
                    }

                # When completed or failed, close the stream cleanly
                if status in SSE_TERMINAL_STATUSES:
                    break

                elapsed += SSE_POLL_INTERVAL_SECONDS
                if elapsed >= SSE_MAX_DURATION_SECONDS:
                    yield {
                        "event": "timeout",
                        "data": json.dumps({"job_id": job_id, "reason": "max_duration"}),
                    }
                    break

                # ✅ CRITICAL: Cooperative async sleep yields control to Uvicorn, flushes socket buffers
                await asyncio.sleep(SSE_POLL_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            raise
        except Exception as exc:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
        ping=10,  # Ping frame every 10s prevents proxy drop during long LLM ranking
    )
