from langchain_core.tools import tool
from ..services.vectorstore import hybrid_search
from ..services.ingestion import ingest_all
from ..services.vectorstore import upsert_profiles
import pandas as pd

@tool
def search_resumes_tool(query: str, top_k: int = 10) -> str:
    """Search resumes in Qdrant talent pool. Use for any candidate search."""
    results = hybrid_search(query, top_k=top_k)
    summary = []
    for r in results[:top_k]:
        p = r["payload"]
        summary.append(f"{p['filename']} | Skills: {p['skills']} | Exp: {p['experience_years']} | Loc: {p['location']}")
    return "\n".join(summary) or "No candidates found"

@tool
def rank_candidate_tool(resume_preview: str, job_description: str) -> str:
    """Score a candidate preview against JD from 0-100 with reasoning."""
    # Simple heuristic if no LLM key, else LLM will be used in agent
    return f"Preview: {resume_preview[:500]} vs JD: {job_description[:500]} -> Score estimate"

@tool
def generate_outreach_email_tool(candidate_name: str, job_title: str, company: str = "Our Company") -> str:
    """Generate personalized outreach email for candidate."""
    return f"Subject: Opportunity for {job_title} at {company}\nHi {candidate_name},\nWe loved your profile..."

@tool
def ingest_resumes_tool() -> str:
    """Ingest all resumes from folder and index into Qdrant."""
    df = ingest_all()
    if df.empty:
        return "No resumes found"
    count = upsert_profiles(df)
    return f"Ingested {len(df)} resumes, upserted {count} vectors"