# backend/app/services/chat_service.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from app.core.llm import get_smart_llm, get_fast_llm
from app.services.vectorstore import hybrid_search, COLLECTION_NAME
from app.core.qdrant import get_qdrant_client

SYSTEM_PROMPT = """You are Rabbit Hire's AI Talent Intelligence Recruiter.
You assist hiring managers in searching, evaluating, and drilling down into candidates indexed in the company's talent pool.

You have access to two tools:
1. `search_talent_pool`: Use this when the user is searching for candidates by skills, job title, experience, or location.
2. `get_candidate_profile`: Use this when the user asks about a specific person by name.

Guidelines:
- If the user says "hi", "hello", or asks general questions, respond conversationally and professionally. Do NOT call tools for pleasantries.
- When answering follow-up questions about a candidate who was already discussed in the conversation (e.g. "where he is from", "what is his email", "does he know React"), use the information already present in the conversation history. Only call `get_candidate_profile` if you need missing information.
- Format candidate overviews clearly using bullet points. Do NOT use markdown tables.
- Always be accurate to the resume text. Do not invent experience or skills.
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
            with_vectors=False
        )
    except Exception:
        return None

    target = _normalize_name(name)
    target_tokens = set(target.split())

    for r in recs:
        p = r.payload or {}
        cand_str = _normalize_name(
            (p.get("name") or "") + " " + (p.get("filename") or ""))
        cand_tokens = set(cand_str.split())

        if target and (target in cand_str or cand_str in target or target_tokens.issubset(cand_tokens)):
            return {
                "id": str(r.id),
                "payload": p
            }
    return None


class ChatAgentRunner:
    """Thread-safe runner for a conversational tool-calling turn."""

    def __init__(self):
        self.retrieved_candidates: List[Dict[str, Any]] = []

    def get_tools(self):
        @tool
        def search_talent_pool(query: str) -> str:
            """Search the talent pool for candidates matching job titles, skills, locations, or experience."""
            docs = hybrid_search(query=query, top_k=5)
            if not docs:
                return "No candidates found matching the query."

            formatted = []
            for doc in docs:
                p = doc.get("payload", {})
                self.retrieved_candidates.append(p)
                name = p.get("name") or p.get("filename", "Unknown")
                exp = p.get("experience", "?")
                loc = ", ".join(p.get("location") or []) or "Unknown"
                skills = ", ".join(p.get("skills") or [])[:120]
                formatted.append(
                    f"- Name: {name} | Exp: {exp} yrs | Location: {loc} | Skills: {skills}")

            return "\n".join(formatted)

        @tool
        def get_candidate_profile(name: str) -> str:
            """Get the full resume, contact details, experience, and background for a candidate by name."""
            cand = search_by_name(name)
            if not cand:
                return f"No candidate named '{name}' found in the database."

            p = cand["payload"]
            self.retrieved_candidates.append(p)

            return json.dumps({
                "name": p.get("name") or p.get("filename"),
                "email": p.get("email"),
                "phone": p.get("phone"),
                "location": p.get("location"),
                "experience_years": p.get("experience"),
                "skills": p.get("skills"),
                "summary": p.get("summary"),
                "resume_excerpt": (p.get("text") or "")[:4000]
            })

        return [search_talent_pool, get_candidate_profile]

    def run(self, message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
        tools = self.get_tools()
        tools_by_name = {t.name: t for t in tools}

        llm = get_smart_llm(temperature=0.1) or get_fast_llm(temperature=0.1)
        llm_with_tools = llm.bind_tools(tools)

        # 1. Build messages with history
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for turn in history[-10:]:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=message))

        # 2. First invocation (Model decides to answer directly or call tools)
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        # 3. If tools are requested, execute them and make the final invocation
        if ai_msg.tool_calls:
            for tool_call in ai_msg.tool_calls:
                selected_tool = tools_by_name.get(tool_call["name"])
                if selected_tool:
                    tool_output = selected_tool.invoke(tool_call["args"])
                    messages.append(ToolMessage(content=str(
                        tool_output), tool_call_id=tool_call["id"]))

            # Final call: LLM generates the response with tool outputs in context
            final_response = llm.invoke(messages)
            final_answer = getattr(
                final_response, "content", str(final_response))
        else:
            final_answer = getattr(ai_msg, "content", str(ai_msg))

        # 4. Format structured candidates for frontend cards
        candidates_out = []
        seen_filenames = set()
        for p in self.retrieved_candidates:
            fn = p.get("filename")
            if fn and fn not in seen_filenames:
                seen_filenames.add(fn)
                candidates_out.append({
                    "id": fn,
                    "filename": fn,
                    "name": (p.get("name") or fn).replace("_", " ").replace(".pdf", ""),
                    "full_name": p.get("name") or fn,
                    "skills": p.get("skills") or p.get("skills_raw") or [],
                    "location": p.get("location") or [],
                    "experience_years": int(p.get("experience", 0) or 0),
                    "experience": int(p.get("experience", 0) or 0),
                    "email": p.get("email"),
                    "phone": p.get("phone"),
                    "text": p.get("text", "")[:2000],
                })

        return {
            "answer": final_answer,
            "candidates": candidates_out
        }


def execute_chat_turn(message: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    """Single entry point for the chat endpoint."""
    runner = ChatAgentRunner()
    return runner.run(message=message, history=history)
