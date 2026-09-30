# backend/app/services/query_understanding.py
from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.core.llm import get_fast_llm


class ChatIntent(str, Enum):
    SEARCH = "search"
    DETAIL = "detail"
    REFINE = "refine"


class ExtractedQuery(BaseModel):
    intent: ChatIntent = Field(description="search | detail | refine")
    names: List[str] = Field(default_factory=list,
                             description="Person names mentioned")
    locations: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    original_query: str = ""
    rewritten_query: str = ""


SYSTEM = """You are Query Understanding for a talent conversation system.

Extract structured information from the user message + recent history.

Intent rules:
- "detail"  → User is asking about a specific person (by name or referring to previous person with "he/she/his/her")
- "search"  → User is looking for candidates
- "refine"  → Short follow-up that changes filters of the previous search

Rules:
- Always extract full person names when present (prefer "First Last")
- locations: use proper Title Case (Bengaluru, not bangalore)
- required_skills: only when the user makes a skill mandatory
- rewritten_query: clean version useful for search

When the user uses pronouns like "he", "his", "she", "that guy" and a person was discussed recently, still set intent="detail".

Return ONLY valid JSON.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("human", "Message: {message}\n\nRecent history:\n{history}")
])


def understand_query(message: str, history: list[dict] | None = None) -> ExtractedQuery:
    history = history or []
    llm = get_fast_llm(temperature=0)

    if not llm:
        return ExtractedQuery(
            intent=ChatIntent.SEARCH,
            original_query=message,
            rewritten_query=message
        )

    structured_llm = llm.with_structured_output(ExtractedQuery)
    chain = prompt | structured_llm

    try:
        # Keep history short and useful
        history_text = ""
        for turn in history[-6:]:
            role = turn.get("role", "")
            content = turn.get("content") or turn.get("message") or ""
            history_text += f"{role}: {content}\n"

        result = chain.invoke({
            "message": message[:1500],
            "history": history_text or "None"
        })

        result.original_query = message
        if not result.rewritten_query:
            result.rewritten_query = message

        return result

    except Exception as e:
        print(f"[QUERY_UNDERSTANDING] {e}")
        return ExtractedQuery(
            intent=ChatIntent.SEARCH,
            original_query=message,
            rewritten_query=message
        )
