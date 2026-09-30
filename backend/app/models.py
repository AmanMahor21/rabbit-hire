from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid

Base = declarative_base()


class HireJob(Base):
    __tablename__ = "hire_jobs"
    id = Column(String, primary_key=True,
                default=lambda: uuid.uuid4().hex[:12])
    user_id = Column(String, index=True)  # from auth
    # queued, running, completed, failed, cancelled
    status = Column(String, default="queued")
    stage = Column(String, default="queued")  # search, ranker, outreach
    progress = Column(Integer, default=0)
    jd_hash = Column(String, index=True)  # for idempotency / cache
    payload = Column(JSON)  # {jd, top_k, auto_outreach}
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


class ExperienceRange(BaseModel):
    min_years: int = 0
    max_years: int = 50


class SearchFilters(BaseModel):
    skills: List[str] = []
    locations: List[str] = []
    domains: List[str] = []
    degrees: List[str] = []
    experience: int = 0
    strict_skill_search: bool = False  # deprecated, keep False for recall
    has_clearance: bool = False


class SearchRequest(BaseModel):
    query: str = ""
    filters: SearchFilters = Field(default_factory=SearchFilters)
    top_k: int = 50


class RankingRequest(BaseModel):
    query: str
    filters: SearchFilters
    candidates: List[Dict[str, Any]]
    job_description: str


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    filters: Optional[SearchFilters] = None


class AgentStateEnum(str, Enum):
    PARSER = "parser"
    SEARCH = "search"
    RANKER = "ranker"
    OUTREACH = "outreach"


class AgenticHireRequest(BaseModel):
    job_description: str
    top_k: int = 5
    auto_generate_outreach: bool = True


class CandidateScore(BaseModel):
    filename: str
    ai_score: int = Field(ge=0, le=100)
    summary: str
    pros: str
    cons: str
    key_risk: str = "None"
    loyalty_score: int = Field(ge=0, le=10, default=5)
    loyalty_analysis: str = ""
    job_stability_analysis: str = ""
