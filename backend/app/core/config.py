# backend/app/core/config.py
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Agentic Talent Platform")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    MIN_SIMILARITY: float = float(os.getenv("MIN_SIMILARITY", "0.35"))
    SCORE_GAP: float = float(os.getenv("SCORE_GAP", "0.15"))
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))
    RESUME_DIR: str = os.getenv("RESUME_DIR", "./resumes")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./qdrant_data")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "resume_profiles")
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


settings = Settings()
