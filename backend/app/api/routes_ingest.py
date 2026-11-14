# backend/app/api/routes_ingest.py
from __future__ import annotations
from celery.result import AsyncResult
from ..tasks.ingest_tasks import process_resumes_task
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.ingestion import ingest_all, get_existing_file_hashes, get_file_hash
from ..services.vectorstore import upsert_profiles, get_client, COLLECTION_NAME
from ..core.config import settings
import pandas as pd
from .routes_search import _EXPERIENCE_BUCKETS, _bucket_experience

router = APIRouter()
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _safe_filename(raw_filename: str) -> str:
    name = Path(raw_filename).name.strip()
    if not name or name in {".", ".."}:
        raise ValueError("Invalid filename")
    return name


async def _save_upload(file: UploadFile, destination: Path) -> bool:
    size = 0
    try:
        with open(destination, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE_BYTES:
                    return False
                out.write(chunk)
        return True
    finally:
        if size > MAX_FILE_SIZE_BYTES and destination.exists():
            destination.unlink(missing_ok=True)


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    os.makedirs(settings.RESUME_DIR, exist_ok=True)
    resume_dir = Path(settings.RESUME_DIR).resolve()
    saved = 0
    skipped: list[str] = []
    for f in files:
        if not f.filename:
            continue
        try:
            safe_name = _safe_filename(f.filename)
        except ValueError:
            skipped.append(f.filename)
            continue
        extension = Path(safe_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            skipped.append(safe_name)
            continue
        destination = (resume_dir / safe_name).resolve()
        if resume_dir != destination and resume_dir not in destination.parents:
            skipped.append(safe_name)
            continue
        ok = await _save_upload(f, destination)
        if ok:
            saved += 1
        else:
            skipped.append(safe_name)
    return {"message": f"Saved {saved} files", "skipped": skipped}


@router.post("/process")
async def process_resumes():
    """Trigger async ingestion - returns immediately."""
    # Check if already running (optional: use Redis lock or DB flag)
    result = process_resumes_task.delay()

    return {
        "message": "Processing started in background",
        "task_id": result.id,
        "status": "queued"
    }

# backend/app/api/routes_ingest.py


@router.get("/process/status/{task_id}")
async def get_process_status(task_id: str):
    result = AsyncResult(task_id, app=process_resumes_task.app)

    if result.ready():
        if result.successful():
            return {"status": "completed", "result": result.result}
        else:
            return {"status": "failed", "error": str(result.result)}

    return {"status": "processing", "state": result.state}


@router.get("/process/pending")
async def get_pending_process():
    """Count resumes that have been uploaded but not yet indexed.

    We reuse the same hash comparison the ingest task uses: a file is
    "pending" if it exists on disk and its current hash differs from the
    hash stored in Qdrant (or it has no entry at all).
    """
    if not os.path.isdir(settings.RESUME_DIR):
        return {"pending": 0, "total": 0}

    resume_dir = Path(settings.RESUME_DIR).resolve()
    files = [
        f for f in os.listdir(resume_dir)
        if os.path.isfile(resume_dir / f)
        and Path(f).suffix.lower() in ALLOWED_EXTENSIONS
    ]

    existing_hashes = get_existing_file_hashes()
    pending = 0
    for filename in files:
        filepath = resume_dir / filename
        try:
            current_hash = get_file_hash(str(filepath))
        except Exception:
            continue
        if existing_hashes.get(filename) != current_hash:
            pending += 1

    return {"pending": pending, "total": len(files)}


@router.get("/stats")
async def stats():
    files = [f for f in os.listdir(settings.RESUME_DIR) if os.path.isfile(
        os.path.join(settings.RESUME_DIR, f))]
    records = []
    try:
        col_info = get_client().get_collection(COLLECTION_NAME)
        parsed = col_info.points_count
        records, _ = get_client().scroll(
            collection_name=COLLECTION_NAME, limit=1000, with_payload=True, with_vectors=False)
        all_sk = set(s for r in records for s in (
            r.payload.get("skills", []) or []))
        unique = len(all_sk)
    except Exception:
        parsed = 0
        unique = 0
    charts = {}
    if records:
        skills_series = pd.Series(
            s for r in records for s in (r.payload.get("skills", []) or []))
        top_skills = skills_series.value_counts().head(10)
        bucket_counts = {b: 0 for b in _EXPERIENCE_BUCKETS}
        for r in records:
            bucket_counts[_bucket_experience(
                int(r.payload.get("experience", 0) or 0))] += 1
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
    return {"total_resumes": len(files), "parsed_resumes": parsed,
            "unique_skills": unique, "charts": charts}
