# backend/app/agents/search_agent.py
from __future__ import annotations
import os
from typing import Any
from app.services.vectorstore import hybrid_search

USE_LLM_QUERY_REWRITE = os.getenv(
    "USE_LLM_QUERY_REWRITE", "false").lower() == "true"


def rewrite_query_with_llm(query: str) -> str:
    try:
        from app.core.llm import get_fast_llm
        llm = get_fast_llm(temperature=0)
        prompt = f"""
Rewrite this hiring query for semantic resume search.
Expand relevant technical synonyms.
Return ONLY the rewritten query.
Hiring query:
{query[:2000]}
"""
        response = llm.invoke(prompt)
        rewritten = getattr(response, "content", "").strip()
        return rewritten or query
    except Exception as exc:
        print(f"Query rewrite failed: {exc}")
        return query


def search_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    query = str(state.get("query", "")).strip()
    top_k = int(state.get("top_k", 5) or 5)
    top_k = max(1, min(top_k, 20))
    filters = state.get("filters")

    if not query:
        return {"search_results": [], "rewritten_query": ""}

    rewritten_query = query
    if USE_LLM_QUERY_REWRITE:
        rewritten_query = rewrite_query_with_llm(query)

    results = hybrid_search(query=rewritten_query,
                            top_k=top_k, filters=filters)

    return {
        "search_results": results,
        "rewritten_query": rewritten_query,
    }
