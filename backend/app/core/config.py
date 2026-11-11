# backend/app/core/config.py
from __future__ import annotations
import os
import socket
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def resolve_service_url(url: str, default_local_host: str = "localhost") -> str:
    """
    Checks if the hostname in a service URL (e.g. 'postgres', 'redis', 'qdrant')
    is resolvable via DNS. When running outside Docker containers, internal container
    hostnames fail DNS resolution; this automatically maps them to 'localhost' so the
    application works seamlessly in both containerized and local environments.
    """
    if not url or not isinstance(url, str):
        return url
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return url
        try:
            socket.gethostbyname(host)
            return url
        except socket.gaierror:
            port_str = f":{parsed.port}" if parsed.port is not None else ""
            userinfo = ""
            if parsed.username or parsed.password:
                user = parsed.username or ""
                pwd = f":{parsed.password}" if parsed.password else ""
                userinfo = f"{user}{pwd}@"
            new_netloc = f"{userinfo}{default_local_host}{port_str}"
            return urlunparse(parsed._replace(netloc=new_netloc))
    except Exception:
        return url


@dataclass
class Settings:
    DATABASE_URL: str = resolve_service_url(
        os.getenv(
            "DATABASE_URL",
            "postgresql://talent:talent@localhost:5432/talent",
        )
    )
    REDIS_URL: str = resolve_service_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    APP_NAME: str = os.getenv("APP_NAME", "Agentic Talent Platform")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    MIN_SIMILARITY: float = float(os.getenv("MIN_SIMILARITY", "0.35"))
    SCORE_GAP: float = float(os.getenv("SCORE_GAP", "0.15"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))
    RESUME_DIR: str = os.getenv("RESUME_DIR", "./resumes")
    QDRANT_URL: str = resolve_service_url(os.getenv("QDRANT_URL", ""))
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./qdrant_data")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    QDRANT_COLLECTION: str = os.getenv(
        "QDRANT_COLLECTION", "resume_profiles")
    SKILL_TAXONOMY_COLLECTION: str = os.getenv(
        "SKILL_TAXONOMY_COLLECTION", "skill_taxonomy")
    SKILL_SIMILARITY_THRESHOLD: float = float(
        os.getenv("SKILL_SIMILARITY_THRESHOLD", "0.85"))
    RERANK_MODEL: str = os.getenv(
        "RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    LLM_API_KEY: str = os.getenv(
        "LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_FAST_MODEL: str = os.getenv("LLM_FAST_MODEL", "gpt-4o-mini")
    LLM_SMART_MODEL: str = os.getenv("LLM_SMART_MODEL", "gpt-4o")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "800"))
    LLM_STUB: bool = os.getenv("LLM_STUB", "false").lower() == "true"
    ENABLE_METRICS: bool = os.getenv(
        "ENABLE_METRICS", "true").lower() == "true"


settings = Settings()
