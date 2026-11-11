# backend/app/main.py
from prometheus_fastapi_instrumentator import Instrumentator
from app.db import init_db
from app.core.config import settings
from app.core.llm import is_llm_configured
from app.api import routes_ingest, routes_search, routes_agents, routes_chat, routes_filters, routes_eval
from prometheus_client import Gauge
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logging import configure_logging
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Agentic Talent Platform - GenAI + Agentic AI",
    version="2.0",
    description="Autonomous hiring with LangGraph, Qdrant, RAG, and Multi-Agent system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip()
                   for x in settings.CORS_ORIGINS.split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_ingest.router, prefix="/api", tags=["Ingest"])
app.include_router(routes_search.router, prefix="/api", tags=["Search"])
app.include_router(routes_agents.router, prefix="/api", tags=["Agents"])
app.include_router(routes_chat.router, prefix="/api", tags=["Chat"])
app.include_router(routes_filters.router, prefix="/api", tags=["filters"])
app.include_router(routes_eval.router, prefix="/api", tags=["eval"])

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    excluded_handlers=["/metrics", "/health"],
)

instrumentator.instrument(app).expose(app, endpoint="/metrics")

SYSTEM_UP = Gauge(
    "rabbithire_system_up",
    "1 if critical dependencies (PostgreSQL, Qdrant, Redis) are reachable",
)


def _probe_db() -> bool:
    try:
        from app.db import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _probe_qdrant() -> bool:
    try:
        from app.services.vectorstore import get_client
        get_client().get_collections()
        return True
    except Exception:
        return False


def _probe_redis() -> bool:
    try:
        import redis as _redis
        r = _redis.from_url(settings.REDIS_URL, socket_timeout=0.5)
        r.ping()
        return True
    except Exception:
        return False


@app.get("/")
def root():
    return {
        "message": "Agentic Talent Platform v2 running",
        "features": ["Qdrant Hybrid Search", "LangGraph Supervisor", "Celery Queue", "SSE Progress"],
        "docs": "/docs"
    }


@app.get("/health")
def health():
    db_ok = _probe_db()
    qdrant_ok = _probe_qdrant()
    redis_ok = _probe_redis()
    healthy = db_ok and qdrant_ok and redis_ok

    SYSTEM_UP.set(1 if healthy else 0)

    return {
        "status": "ok" if healthy else "degraded",
        "database": "up" if db_ok else "down",
        "qdrant": "up" if qdrant_ok else "down",
        "redis": "up" if redis_ok else "down",
        "llm_configured": is_llm_configured(),
    }
