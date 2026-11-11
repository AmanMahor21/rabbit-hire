# backend/app/api/routes_eval.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.db import get_db
from app.models import EvalFeedback, SearchLog, EvalRun
from app.eval.runners.test_search import run_search_eval_detailed
# from app.eval.error_analysis import generate_error_report

router = APIRouter(tags=["Eval"])


class FeedbackRequest(BaseModel):
    type: str  # search, rank, chat, outreach
    human_rating: int  # 1-5
    query: Optional[str] = None
    job_id: Optional[str] = None
    candidate_filename: Optional[str] = None
    notes: Optional[str] = None
    error_tags: Optional[List[str]] = None
    meta: Optional[dict] = None


class SearchLogRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    results: List[str]
    clicked_filename: Optional[str] = None


@router.post("/eval/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    try:
        fb = EvalFeedback(
            type=req.type,
            human_rating=req.human_rating,
            query=req.query,
            job_id=req.job_id,
            candidate_filename=req.candidate_filename,
            notes=req.notes,
            error_tags=req.error_tags,
            meta=req.meta
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return {"id": fb.id, "status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eval/search-log")
def log_search(req: SearchLogRequest, db: Session = Depends(get_db)):
    log = SearchLog(query=req.query, filters=req.filters,
                    results=req.results, clicked_filename=req.clicked_filename)
    db.add(log)
    db.commit()
    return {"id": log.id}


@router.get("/eval/metrics")
def get_eval_metrics(db: Session = Depends(get_db)):
    # Run live eval
    search_results = run_search_eval_detailed()
    avg_recall = sum(r["recall"] for r in search_results) / \
        len(search_results) if search_results else 0
    avg_prec = sum(r["precision"] for r in search_results) / \
        len(search_results) if search_results else 0

    # Get human feedback stats
    feedbacks = db.query(EvalFeedback).all()
    avg_human = sum(f.human_rating for f in feedbacks) / \
        len(feedbacks) if feedbacks else 0

    return {
        "automated": {
            "search_cases": len(search_results),
            "avg_recall": avg_recall,
            "avg_precision": avg_prec,
            "pass_rate": sum(1 for r in search_results if r["pass"]) / len(search_results) if search_results else 0
        },
        "human": {
            "total_feedbacks": len(feedbacks),
            "avg_rating": avg_human
        },
        "details": search_results[:10]
    }


@router.get("/eval/feedbacks")
def list_feedbacks(limit: int = 50, db: Session = Depends(get_db)):
    fbs = db.query(EvalFeedback).order_by(
        EvalFeedback.created_at.desc()).limit(limit).all()
    return [
        {
            "id": fb.id,
            "type": fb.type,
            "query": fb.query,
            "human_rating": fb.human_rating,
            "notes": fb.notes,
            "error_tags": fb.error_tags,
            "created_at": fb.created_at
        } for fb in fbs
    ]


@router.post("/eval/run")
def trigger_eval_run(db: Session = Depends(get_db)):
    search_results = run_search_eval_detailed()
    failed = [r for r in search_results if not r["pass"]]

    metrics = {
        "search": {
            "avg_recall": sum(r["recall"] for r in search_results) / len(search_results) if search_results else 0,
            "failed_count": len(failed)
        }
    }

    run = EvalRun(trigger="manual", metrics=metrics,
                  passed="pass" if len(failed) == 0 else "fail")
    db.add(run)
    db.commit()

    return {"run_id": run.id, "metrics": metrics, "failed_cases": failed[:5]}
