from warnings import filters

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_ingest, routes_search, routes_agents, routes_chat, routes_filters
from app.core.llm import is_llm_configured
from app.models import Base
from app.db import engine

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic Talent Platform - GenAI + Agentic AI",
    version="2.0",
    description="Autonomous hiring with LangGraph, Qdrant, RAG, and Multi-Agent system"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_ingest.router, prefix="/api", tags=["Ingest"])
app.include_router(routes_search.router, prefix="/api", tags=["Search"])
app.include_router(routes_agents.router, prefix="/api", tags=["Agents"])
app.include_router(routes_chat.router, prefix="/api", tags=["Chat"])
app.include_router(routes_filters.router, prefix="/api", tags=["filters"])


@app.get("/")
def root():
    return {
        "message": "Agentic Talent Platform v2 running",
        "features": ["Qdrant Hybrid Search", "LangGraph Supervisor", "Celery Queue", "SSE Progress"],
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "ok", "qdrant": "in-memory ready", "llm_configured": is_llm_configured()}
