# backend/app/core/llm_stub.py
"""
Deterministic LLM stand-in used when LLM_STUB=true.
Returns content that the existing parsers/rankers can consume without
touching OpenAI. NOT for production — dev/load-test only.
"""
from __future__ import annotations
import json
import re
import time
import random
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FakeAIMessage:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    response_metadata: dict[str, Any] = field(default_factory=dict)


class _FakeChain:
    """Mimics `prompt | llm` — just returns the LLM."""

    def __init__(self, llm): self._llm = llm

    def invoke(self, inputs):
        return self._llm.invoke(inputs)


class StubLLM:
    """
    Drop-in for ChatOpenAI used by agents/chat.
    Behavior is decided by inspecting the prompt text.
    """

    def __init__(self, model: str, temperature: float = 0.0, **_):
        self.model = model
        self.temperature = temperature
        self._latency = float(__import__("os").getenv(
            "LLM_STUB_LATENCY_MS", "0")) / 1000.0

    # -- fake "chat" invocation -------------------------------------------------
    def invoke(self, messages, **_) -> FakeAIMessage:
        if self._latency:
            time.sleep(self._latency + random.uniform(0, self._latency * 0.2))
        text = self._flatten(messages)
        return FakeAIMessage(content=self._route(text))

    # -- streaming (for the future /chat/stream endpoint) ----------------------
    async def ainvoke(self, messages, **_) -> FakeAIMessage:
        return self.invoke(messages)

    def _route(self, text: str) -> str:
        t = text.lower()

        # 1. Parser agent
        if "resume parser" in t or ("return only valid json" in t and "skills" in t and "experience_years" in t):
            return json.dumps({
                "skills": ["PYTHON", "FASTAPI", "QDRANT", "LANGCHAIN"],
                "experience_years": 4,
                "location": ["Bengaluru"],
                "domains": ["Backend"],
                "education": ["BACHELORS"],
                "summary": "Stub summary.",
            })

        # 2. Ranker agent
        if "expert technical recruiter" in t or ('"score"' in t and '"matched_skills"' in t):
            return json.dumps({
                "score": random.randint(40, 95),
                "reason": "Stub ranking reason.",
                "matched_skills": ["PYTHON"],
                "missing_skills": ["KUBERNETES"],
            })

        # 3. Outreach agent
        if "recruiter outreach email" in t or "100-150 words" in t:
            return "Hi there,\n\nStub outreach body for load testing.\n\nBest,\nRecruiting Team"

        # 4. Query understanding (structured output)
        if "query understanding" in t or "extractedquery" in t or "intent rules" in t:
            return json.dumps({
                "intent": "search",
                "names": [], "locations": [],
                "skills": ["PYTHON"], "required_skills": [],
                "min_experience": None, "max_experience": None,
                "original_query": "", "rewritten_query": "python developer",
            })

        # 5. LLM-as-judge
        if "expert evaluator" in t:
            return json.dumps({"rating": 4, "faithful": True, "error_tags": [], "comment": "stub"})

        # 6. Chat / general fallback
        return "Stub chat answer. Found 3 candidates matching your query."

    # -- helpers ----------------------------------------------------------------
    def _flatten(self, messages) -> str:
        # Accept either str, list[BaseMessage], or list[dict]
        if isinstance(messages, str):
            return messages
        chunks = []
        for m in messages or []:
            if isinstance(m, str):
                chunks.append(m)
            elif isinstance(m, dict):
                chunks.append(str(m.get("content", "")))
            else:
                chunks.append(str(getattr(m, "content", "")))
        return "\n".join(chunks)

    # -- LangChain surface ------------------------------------------------------
    def with_structured_output(self, schema, **_):
        """
        understand_query calls:  llm.with_structured_output(ExtractedQuery)
        It then does  chain = prompt | structured_llm  and  chain.invoke(...)
        We must return something whose .invoke returns an ExtractedQuery instance,
        not JSON text.
        """
        stub = self

        class _Structured:
            def invoke(self, inputs):
                raw = stub.invoke(inputs).content
                data = json.loads(raw)
                # Instantiate the pydantic model defensively
                try:
                    return schema(**data)
                except Exception:
                    # Import lazily to avoid circular import if schema differs
                    from app.services.query_understanding import ExtractedQuery, ChatIntent
                    return ExtractedQuery(
                        intent=ChatIntent.SEARCH,
                        original_query=data.get("rewritten_query", ""),
                        rewritten_query=data.get("rewritten_query", ""),
                    )

            async def ainvoke(self, inputs):
                return self.invoke(inputs)

        return _Structured()

    def bind_tools(self, tools):
        """
        chat_service does llm.bind_tools(tools).invoke(messages).
        We *could* emit fake tool_calls, but simpler and more honest:
        return self — the chat runner's `_deterministic_search` already
        runs a real hybrid_search first, then llm.invoke() formats text.
        Our normal `_route` returns a plain chat answer, which is enough.
        """
        return self

    def __or__(self, other):  # prompt | llm
        return _FakeChain(self)
