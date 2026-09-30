# backend/app/api/routes_chat.py - PRODUCTION SAAS
from __future__ import annotations
from fastapi import APIRouter
from app.models import ChatRequest
from app.services.query_understanding import understand_query
from app.services.chat_service import search_and_answer, search_production
from app.services.vectorstore import COLLECTION_NAME
from app.core.qdrant import get_qdrant_client

router = APIRouter()


def build_candidates(docs):
    out = []
    for r in docs:
        p = r.get("payload", {})
        out.append({
            "filename": p.get("filename", ""), "name": (p.get("name") or p.get("filename", "")).replace("_", " ").replace(".pdf", ""),
            "skills": p.get("skills", []) or p.get("skills_raw", []), "location": p.get("location", []),
            "experience_years": int(p.get("experience", 0) or 0), "experience": int(p.get("experience", 0) or 0),
            "email": p.get("email"), "phone": p.get("phone"), "text": p.get("text", "")[:2000],
            "score": r.get("rerank_score", 0), "rank_score": r.get("rerank_score", 0)
        })
    return out


@router.post("/chat")
async def chat_with_talent(req: ChatRequest):
    msg = (req.message or "").strip()

    extracted = understand_query(msg, req.history)

    result = search_and_answer(
        extracted=extracted,
        history=req.history,
        top_k=8
    )

    return {
        "answer": result["answer"],
        "candidates": result["candidates"],
        "focused_candidate": result.get("focused_candidate"),
        "intent": result["intent"],
        "mode": result["mode"],
        "parsed_query": extracted.model_dump()
    }


@router.get("/chat/health")
async def chat_health():
    client = get_qdrant_client()
    info = client.get_collection(COLLECTION_NAME)
    return {"collection": COLLECTION_NAME, "points": info.points_count}
