# backend/app/services/chat_service.py
"""
Talent Chat — production path.

FAANG-level changes vs previous version:
  - Query understanding runs BEFORE tool selection (structured intent + filters)
  - search_talent_pool accepts locations / min_experience / skills and passes
    real filters into hybrid_search (same path as /api/search)
  - Location aliases resolved via shared location_normalize
  - Tool returns structured multi-candidate text; system prompt forces listing all
  - Deterministic SEARCH hop when intent is clear (optional, reduces LLM drift)
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from app.core.llm import get_fast_llm, get_smart_llm
from app.core.qdrant import get_qdrant_client
from app.services.location_normalize import expand_for_filter, normalize_locations
from app.services.query_understanding import ChatIntent, understand_query
from app.services.vectorstore import COLLECTION_NAME, hybrid_search

SYSTEM_PROMPT = """You are Rabbit Hire's AI Talent Intelligence Recruiter.
You assist hiring managers in searching, evaluating, and drilling down into candidates indexed in the company's talent pool.

You have access to two tools:
1. `search_talent_pool`: Use when the user is searching for candidates by skills, job title, experience, or location.
2. `get_candidate_profile`: Use when the user asks about a specific person by name.

Guidelines:
- If the user says "hi", "hello", or asks general questions, respond conversationally. Do NOT call tools for pleasantries.
- When answering follow-up questions about a candidate already in history (e.g. "what is his email"), use conversation context first; only call get_candidate_profile if data is missing.
- When search_talent_pool returns candidates, list EVERY candidate returned (name, experience, location, key skills). Do NOT collapse to a single "best" match unless the user explicitly asks for top 1.
- Treat Bangalore and Bengaluru as the same city. Prefer structured filters (locations, min_experience) over stuffing everything into free text.
- Be accurate to resume data. Do not invent skills or experience.
- Format candidate overviews with bullet points. Do NOT use markdown tables.
"""


def _normalize_name(name: str) -> str:
    return " ".join(
        name.lower()
        .replace("_", " ")
        .replace(".pdf", "")
        .replace("-", " ")
        .split()
    )


def search_by_name(name: str) -> Optional[dict]:
    """Exact/fuzzy lookup for a candidate in Qdrant by name."""
    client = get_qdrant_client()
    try:
        recs, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1500,
            with_payload=True,
            with_vectors=False,
        )
    except Exception:
        return None

    target = _normalize_name(name)
    target_tokens = set(target.split())

    for r in recs:
        p = r.payload or {}
        cand_str = _normalize_name(
            (p.get("name") or "") + " " + (p.get("filename") or "")
        )
        cand_tokens = set(cand_str.split())
        if target and (
            target in cand_str
            or cand_str in target
            or target_tokens.issubset(cand_tokens)
        ):
            return {"id": str(r.id), "payload": p}
    return None


def _format_docs_for_llm(docs: List[Dict[str, Any]]) -> str:
    if not docs:
        return "No candidates found matching the query and filters."
    lines = [
        f"Found {len(docs)} candidates (list ALL of them in your answer):"]
    for doc in docs:
        p = doc.get("payload") or {}
        name = p.get("name") or p.get("filename") or "Unknown"
        exp = p.get("experience", "?")
        loc = ", ".join(p.get("location") or []) or "Unknown"
        skills = ", ".join((p.get("skills") or [])[:10])
        score = doc.get("rerank_score", doc.get("score", 0))
        lines.append(
            f"- {name} | Exp: {exp} yrs | Loc: {loc} | Skills: {skills} | score={float(score):.3f}"
        )
    return "\n".join(lines)


def _payload_to_candidate(p: Dict[str, Any]) -> Dict[str, Any]:
    fn = p.get("filename") or ""
    return {
        "id": fn or p.get("name") or "",
        "filename": fn,
        "name": (p.get("name") or fn).replace("_", " ").replace(".pdf", ""),
        "full_name": p.get("name") or fn,
        "skills": p.get("skills") or p.get("skills_raw") or [],
        "location": p.get("location") or [],
        "experience_years": int(p.get("experience", 0) or 0),
        "experience": int(p.get("experience", 0) or 0),
        "email": p.get("email"),
        "phone": p.get("phone"),
        "text": (p.get("text") or "")[:2000],
        "summary": p.get("summary") or "",
    }


class ChatAgentRunner:
    """Thread-safe runner for one conversational tool-calling turn."""

    def __init__(self) -> None:
        self.retrieved_candidates: List[Dict[str, Any]] = []

    def get_tools(self):
        runner = self

        @tool
        def search_talent_pool(
            query: str,
            locations: Optional[List[str]] = None,
            min_experience: Optional[int] = None,
            skills: Optional[List[str]] = None,
            top_k: int = 8,
        ) -> str:
            """Search the talent pool. Pass structured locations and min_experience when the user specifies them. Locations may be Bangalore/Bengaluru/BLR — they are normalized internally."""
            filters: Dict[str, Any] = {}
            locs = normalize_locations(locations) if locations else []
            if not locs and locations:
                # still pass raw for expand_for_filter inside vectorstore
                filters["locations"] = list(locations)
            elif locs:
                # Pass display + aliases so both old and new payloads match
                filters["locations"] = expand_for_filter(locations)

            if min_experience is not None and int(min_experience) > 0:
                filters["experience"] = int(min_experience)
            if skills:
                filters["skills"] = [s for s in skills if s and str(s).strip()]

            q = (query or "").strip()
            if not q and skills:
                q = " ".join(skills)
            if not q:
                q = "developer"

            docs = hybrid_search(
                query=q,
                top_k=max(3, min(int(top_k or 8), 20)),
                filters=filters or None,
            )
            for doc in docs:
                p = doc.get("payload") or {}
                if p:
                    runner.retrieved_candidates.append(p)
            return _format_docs_for_llm(docs)

        @tool
        def get_candidate_profile(name: str) -> str:
            """Get the full resume, contact details, experience, and background for a candidate by name."""
            cand = search_by_name(name)
            if not cand:
                return f"No candidate named '{name}' found in the database."
            p = cand["payload"]
            runner.retrieved_candidates.append(p)
            return json.dumps(
                {
                    "name": p.get("name") or p.get("filename"),
                    "email": p.get("email"),
                    "phone": p.get("phone"),
                    "location": p.get("location"),
                    "experience_years": p.get("experience"),
                    "skills": p.get("skills"),
                    "summary": p.get("summary"),
                    "resume_excerpt": (p.get("text") or "")[:4000],
                }
            )

        return [search_talent_pool, get_candidate_profile]

    def _deterministic_search(self, extracted) -> Optional[str]:
        """
        When intent is clearly SEARCH and we have structured slots,
        run hybrid_search once so the LLM only formats — reduces drift.
        """
        if extracted.intent != ChatIntent.SEARCH:
            return None
        has_structure = bool(
            extracted.locations
            or extracted.min_experience
            or extracted.required_skills
            or extracted.skills
        )
        if not has_structure and not (extracted.rewritten_query or extracted.original_query):
            return None

        tools = {t.name: t for t in self.get_tools()}
        search_tool = tools["search_talent_pool"]
        args = {
            "query": extracted.rewritten_query or extracted.original_query or "",
            "locations": extracted.locations or None,
            "min_experience": extracted.min_experience,
            "skills": (extracted.required_skills or extracted.skills) or None,
            "top_k": 8,
        }
        try:
            return search_tool.invoke(args)
        except Exception as exc:
            print(f"[chat] deterministic search failed: {exc}")
            return None

    def run(self, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        tools = self.get_tools()
        tools_by_name = {t.name: t for t in tools}

        llm = get_smart_llm(temperature=0.1) or get_fast_llm(temperature=0.1)
        if not llm:
            return {
                "answer": "LLM is not configured. Set LLM_API_KEY to enable Talent Chat.",
                "candidates": [],
            }

        # ── 1. Structured understanding (production path) ──
        extracted = understand_query(message, history)

        messages: List[Any] = [SystemMessage(content=SYSTEM_PROMPT)]
        for turn in history[-10:]:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # Enrich user turn with extracted slots so the model sees structure
        enriched = message
        if extracted.intent == ChatIntent.SEARCH and (
            extracted.locations or extracted.min_experience or extracted.skills
        ):
            slot_bits = []
            if extracted.locations:
                slot_bits.append(f"locations={extracted.locations}")
            if extracted.min_experience is not None:
                slot_bits.append(f"min_experience={extracted.min_experience}")
            if extracted.required_skills or extracted.skills:
                slot_bits.append(
                    f"skills={extracted.required_skills or extracted.skills}"
                )
            enriched = (
                f"{message}\n\n[extracted filters for tools: {', '.join(slot_bits)}]"
            )
        messages.append(HumanMessage(content=enriched))

        # ── 2. Deterministic search hop for clear SEARCH intents ──
        pre_result = self._deterministic_search(extracted)
        if pre_result is not None:
            messages.append(
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "search_talent_pool",
                            "args": {
                                "query": extracted.rewritten_query or message,
                                "locations": extracted.locations or [],
                                "min_experience": extracted.min_experience,
                                "skills": extracted.required_skills or extracted.skills or [],
                            },
                            "id": "det_search_1",
                            "type": "tool_call",
                        }
                    ],
                )
            )
            messages.append(
                ToolMessage(content=pre_result, tool_call_id="det_search_1")
            )
            final = llm.invoke(messages)
            final_answer = getattr(final, "content", str(final))
        else:
            # ── 3. Standard tool-calling loop ──
            llm_with_tools = llm.bind_tools(tools)
            ai_msg = llm_with_tools.invoke(messages)
            messages.append(ai_msg)

            if getattr(ai_msg, "tool_calls", None):
                for tool_call in ai_msg.tool_calls:
                    selected = tools_by_name.get(tool_call["name"])
                    if selected:
                        out = selected.invoke(tool_call["args"])
                        messages.append(
                            ToolMessage(
                                content=str(out),
                                tool_call_id=tool_call["id"],
                            )
                        )
                final_response = llm_with_tools.invoke(messages)
                final_answer = getattr(
                    final_response, "content", str(final_response)
                )
            else:
                final_answer = getattr(ai_msg, "content", str(ai_msg))

        # ── 4. Deduped candidates for frontend cards ──
        candidates_out: List[Dict[str, Any]] = []
        seen: set = set()
        for p in self.retrieved_candidates:
            fn = p.get("filename") or p.get("name") or ""
            if fn and fn not in seen:
                seen.add(fn)
                candidates_out.append(_payload_to_candidate(p))

        return {"answer": final_answer, "candidates": candidates_out}


def execute_chat_turn(
    message: str, history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Single entry point for the chat endpoint."""
    runner = ChatAgentRunner()
    return runner.run(message=message, history=history)
