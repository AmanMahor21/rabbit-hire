from app.core.celery_app import celery
from app.graph.supervisor_graph import talent_graph
from app.db import SessionLocal
from app.models import HireJob
import asyncio


@celery.task(bind=True, name="run_hire_graph")
def run_hire_graph(self, job_id: str):
    db = SessionLocal()
    job = db.query(HireJob).filter(HireJob.id == job_id).first()
    if not job:
        db.close()
        return

    async def _run():
        try:
            job.status = "running"
            job.stage = "search"
            job.progress = 10
            db.commit()

            initial_state = {
                "query": job.payload["job_description"][:2000],
                "job_description": job.payload["job_description"][:5000],
                "top_k": job.payload["top_k"],
                "auto_generate_outreach": job.payload["auto_generate_outreach"],
            }

            job.stage = "ranking"
            job.progress = 40
            db.commit()

            result = await talent_graph.ainvoke(initial_state)

            job.stage = "outreach" if job.payload["auto_generate_outreach"] else "finalizing"
            job.progress = 80
            db.commit()

            job.result = {
                "results": result.get("ranked", [])[:job.payload["top_k"]],
                "outreach": result.get("outreach", []),
                "rewritten_query": result.get("rewritten_query", ""),
                "trace": result.get("trace", []),
            }
            job.status = "completed"
            job.progress = 100
            job.stage = "completed"
            db.commit()
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
            job.stage = "failed"
            db.commit()
        finally:
            db.close()

    asyncio.run(_run())
