# backend/app/services/chat_service.py
from __future__ import annotations
from typing import List, Dict, Optional, Any
from app.services.query_understanding import ExtractedQuery, ChatIntent
from app.services.vectorstore import hybrid_search, COLLECTION_NAME
from app.core.qdrant import get_qdrant_client
from app.core.llm import get_fast_llm

# -------------------------------------------------
# Helpers
# -------------------------------------------------


def _normalize_name(name: str) -> str:
    return " ".join(
        name.lower()
        .replace("_", " ")
        .replace(".pdf", "")
        .split()
    )


def _get_last_focused(history: list[dict]) -> Optional[dict]:
    """Return the last focused candidate from conversation history."""
    for turn in reversed(history or []):
        focused = turn.get("focused_candidate")
        if focused:
            return focused
    return None


def _format_candidates_for_llm(candidates: List[Dict]) -> str:
    """Format candidates as a clean bulleted list for the LLM to read."""
    lines = []
    for i, c in enumerate(candidates[:8], 1):
        name = c.get("name") or c.get("filename", "Unknown")
        years = c.get("experience_years") or c.get("experience") or "?"
        loc = ", ".join(c.get("location") or []) or "N/A"
        skills = ", ".join((c.get("skills") or [])[:8])
        # ✅ Use bullet points instead of markdown tables
        lines.append(f"- {name} ({years} yrs, {loc}): {skills}")
    return "\n".join(lines)

# -------------------------------------------------
# Search
# -------------------------------------------------


def search_by_name(name: str, top_k: int = 5) -> List[Dict]:
    """Find candidates whose name or filename matches."""
    client = get_qdrant_client()
    recs, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=1500,
        with_payload=True,
        with_vectors=False
    )
    target = _normalize_name(name)
    matched = []
    for r in recs:
        payload = r.payload or {}
        cand = _normalize_name(
            (payload.get("name") or "") + " " + (payload.get("filename") or "")
        )
        if target and cand and (target in cand or cand in target):
            matched.append({
                "payload": payload,
                "score": 0.99,
                "rerank_score": 0.99
            })
    return matched[:top_k]


def search_production(
    extracted: ExtractedQuery,
    top_k: int = 8,
    history: Optional[list] = None
) -> List[Dict]:
    history = history or []
    # 1. If we have a clear name → try exact-ish name match first
    if extracted.names:
        name_results = search_by_name(extracted.names[0], top_k=top_k)
        if name_results:
            return name_results

    # 2. Fallback to hybrid search
    filters = {}
    if extracted.locations:
        filters["locations"] = extracted.locations
    if extracted.required_skills:
        filters["skills"] = extracted.required_skills
    elif extracted.skills:
        filters["skills"] = extracted.skills
    if extracted.min_experience is not None:
        filters["min_experience"] = extracted.min_experience

    docs = hybrid_search(
        query=extracted.rewritten_query or extracted.original_query,
        top_k=top_k,
        filters=filters or None
    )
    return docs

# -------------------------------------------------
# Natural Answer Generation (the heart of the system)
# -------------------------------------------------


def generate_natural_answer(
    question: str,
    mode: str,
    candidates: List[Dict] = None,
    focused: Optional[dict] = None,
) -> str:
    """
    Let the LLM answer naturally.
    mode = "detail" or "search"
    """
    llm = get_fast_llm(temperature=0.3)
    if not llm:
        return "I'm having trouble generating a response right now."

    if mode == "detail" and focused:
        payload = focused.get("payload") or focused
        name = payload.get("name") or payload.get("filename", "the candidate")
        resume_text = payload.get("text") or ""
        years = payload.get("experience") or payload.get(
            "experience_years") or "unknown"
        location = ", ".join(payload.get("location") or []) or "unknown"
        skills = ", ".join(payload.get("skills") or [])

        prompt = f"""You are a helpful and natural talent assistant.
Answer the user's question using only the information available about this candidate.
If something is not mentioned in the resume, say so clearly and politely.

Candidate: {name}
Experience: {years} years
Location: {location}
Skills: {skills}
Full resume text:
{resume_text[:6500]}

User question: {question}

Respond naturally, like a knowledgeable human recruiter would. Be concise."""

        response = llm.invoke(prompt)
        return getattr(response, "content", str(response)).strip()

    # Search mode
    candidates = candidates or []
    if not candidates:
        return "I couldn't find any candidates matching that."

    # ✅ Updated Prompt: Explicitly forbid tables and enforce natural speech
    prompt = f"""You are a helpful talent search assistant.
Based on the candidates found, answer the user's question naturally and conversationally.
Do not sound like a search engine. Speak like a helpful human.

CRITICAL FORMATTING RULES:
- DO NOT use Markdown tables (no | symbols).
- DO NOT use complex ASCII art.
- Use simple bullet points or short paragraphs.
- Mention names and key skills naturally in sentences.

User question: {question}

Candidates Found:
{_format_candidates_for_llm(candidates)}

Give a natural response. Mention the top matches briefly."""

    response = llm.invoke(prompt)
    return getattr(response, "content", str(response)).strip()

# -------------------------------------------------
# Main entry point used by the API
# -------------------------------------------------


def search_and_answer(
    extracted: ExtractedQuery,
    history: Optional[list] = None,
    top_k: int = 8
) -> dict:
    """
    Main orchestration.
    Returns everything the API needs + the focused candidate for next turn.
    """
    history = history or []
    last_focused = _get_last_focused(history)

    # Resolve who we are talking about
    focused = None
    mode = "search"

    if extracted.intent == ChatIntent.DETAIL or extracted.names:
        mode = "detail"
        if extracted.names:
            results = search_by_name(extracted.names[0], top_k=3)
            if results:
                focused = results[0]
        elif last_focused:
            # User said "he" / "his certificates" etc.
            focused = last_focused

    # Perform search when needed
    candidates = []
    if mode == "search" or (mode == "detail" and not focused):
        docs = search_production(extracted, top_k=top_k, history=history)
        candidates = _build_candidates(docs)

        if mode == "detail" and candidates:
            focused = {
                "name": candidates[0].get("name"),
                "filename": candidates[0].get("filename"),
                "payload": docs[0].get("payload") if docs else candidates[0]
            }

    # Generate natural answer
    answer = generate_natural_answer(
        question=extracted.original_query,
        mode=mode,
        candidates=candidates,
        focused=focused
    )

    return {
        "answer": answer,
        "candidates": candidates if mode == "search" else ([_candidate_from_focused(focused)] if focused else []),
        "focused_candidate": focused,
        "intent": extracted.intent,
        "mode": mode
    }


def _build_candidates(docs: List[Dict]) -> List[Dict]:
    out = []
    for r in docs:
        p = r.get("payload", {})
        out.append({
            "filename": p.get("filename", ""),
            "name": (p.get("name") or p.get("filename", "")).replace("_", " ").replace(".pdf", ""),
            "skills": p.get("skills", []) or p.get("skills_raw", []),
            "location": p.get("location", []),
            "experience_years": int(p.get("experience", 0) or 0),
            "experience": int(p.get("experience", 0) or 0),
            "email": p.get("email"),
            "phone": p.get("phone"),
            "text": p.get("text", "")[:2000],
            "score": r.get("rerank_score", 0),
            "rank_score": r.get("rerank_score", 0)
        })
    return out


def _candidate_from_focused(focused: dict) -> dict:
    if not focused:
        return {}
    p = focused.get("payload") or focused
    return {
        "filename": p.get("filename", ""),
        "name": p.get("name") or p.get("filename", ""),
        "skills": p.get("skills", []),
        "location": p.get("location", []),
        "experience_years": int(p.get("experience", 0) or 0),
        "experience": int(p.get("experience", 0) or 0),
        "text": p.get("text", "")[:2000],
    }
