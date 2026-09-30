from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import hashlib
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

from app.db import get_db
from app.models import HireJob, AgenticHireRequest
from app.tasks.hire_tasks import run_hire_graph
from app.core.redis_client import get_redis

router = APIRouter(tags=["agents"])


@router.post("/agentic-hire", status_code=202)
async def agentic_hire(req: AgenticHireRequest, db: Session = Depends(get_db)):
    # Idempotency check
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

    # This returns immediately, worker does the work
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


@router.get("/agentic-hire")
async def list_hire_jobs(db: Session = Depends(get_db)):
    jobs = db.query(HireJob).order_by(
        HireJob.created_at.desc()).limit(20).all()
    return [
        {
            "job_id": j.id,
            "status": j.status,
            "stage": j.stage,
            "progress": j.progress,
            "created_at": j.created_at,
        } for j in jobs
    ]


@router.get("/agentic-hire/{job_id}/stream")
async def stream_hire_status(job_id: str, db: Session = Depends(get_db)):
    async def generator():
        while True:
            db2 = next(get_db())
            job = db2.query(HireJob).filter(HireJob.id == job_id).first()
            if not job:
                yield {"data": json.dumps({"error": "not found"})}
                break

            yield {"data": json.dumps({
                "job_id": job.id,
                "status": job.status,
                "stage": job.stage,
                "progress": job.progress,
                "result": job.result,
            })}

            if job.status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)

    return EventSourceResponse(generator())
