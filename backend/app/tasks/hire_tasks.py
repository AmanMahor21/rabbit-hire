# backend/app/tasks/hire_tasks.py
from app.core.celery_app import celery
from app.graph.supervisor_graph import talent_graph
from app.db import SessionLocal
from app.models import HireJob
import traceback
from app.core.celery_metrics import measured_task


@celery.task(bind=True, name="run_hire_graph")
@measured_task
def run_hire_graph(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(HireJob).filter(HireJob.id == job_id).first()
        if not job:
            return

        # 1. Search stage (10%)
        job.status = "running"
        job.stage = "search"
        job.progress = 10
        job.error = None
        db.commit()

        initial_state = {
            "query": job.payload["job_description"][:2000],
            "job_description": job.payload["job_description"][:5000],
            "top_k": job.payload["top_k"],
            "auto_generate_outreach": job.payload["auto_generate_outreach"],
        }

        # 2. Ranking stage (40%)
        job.stage = "ranking"
        job.progress = 40
        db.commit()

        try:
            result = talent_graph.invoke(initial_state)
        except Exception as graph_exc:
            tb = traceback.format_exc()
            print(f"[hire_tasks] graph failed for job {job_id}:\n{tb}")
            job.status = "failed"
            job.stage = "failed"
            job.error = f"{type(graph_exc).__name__}: {graph_exc}"
            db.commit()
            return

        # 3. Outreach stage (80%)
        job.stage = "outreach" if job.payload["auto_generate_outreach"] else "finalizing"
        job.progress = 80
        db.commit()

        # 4. Completed (100%)
        job.result = {
            "results": result.get("ranked", [])[: job.payload["top_k"]],
            "outreach": result.get("outreach", []),
            "rewritten_query": result.get("rewritten_query", ""),
            "trace": result.get("trace", []),
        }
        job.status = "completed"
        job.stage = "completed"
        job.progress = 100
        db.commit()
        print(f"[hire_tasks] job {job_id} -> completed successfully (100%)")

    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[hire_tasks] unhandled error for job {job_id}:\n{tb}")
        try:
            job = db.query(HireJob).filter(HireJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.stage = "failed"
                job.error = str(exc)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()
