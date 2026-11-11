# backend/app/core/llm_metrics.py
"""
Thin wrapper that measures any LLM object's .invoke() / .ainvoke() calls.
Does NOT change the LLM's behavior — only records metrics.
"""
from __future__ import annotations

import time
from typing import Any

from app.core.metrics import (
    LLM_FALLBACKS,
    LLM_LATENCY,
    LLM_REQUESTS,
    LLM_TOKENS,
)


def _estimate_tokens(text: Any) -> int:
    """Cheap proxy — 1 token ≈ 4 chars. Good enough for cost trending."""
    if text is None:
        return 0
    if isinstance(text, str):
        return max(1, len(text) // 4)
    # BaseMessage or list of messages
    if hasattr(text, "content"):
        return _estimate_tokens(getattr(text, "content"))
    if isinstance(text, (list, tuple)):
        return sum(_estimate_tokens(x) for x in text)
    return 1


def _extract_model_name(llm: Any) -> str:
    for attr in ("model_name", "model"):
        v = getattr(llm, attr, None)
        if isinstance(v, str) and v:
            return v
    return "unknown"


class MeasuredLLM:
    """
    Pass-through proxy: same .invoke/.ainvoke/.with_structured_output/.bind_tools,
    but records metrics on every call.

    Usage:
        raw = ChatOpenAI(...)
        llm = MeasuredLLM(raw, stage="ranker")
        response = llm.invoke(prompt)   # metrics recorded
    """

    def __init__(self, inner: Any, stage: str):
        self._inner = inner
        self._stage = stage
        self._model = _extract_model_name(inner)

    # ---- core calls ----
    def invoke(self, *args, **kwargs):
        prompt_tokens = _estimate_tokens(
            args[0] if args else kwargs.get("input"))
        start = time.perf_counter()
        try:
            result = self._inner.invoke(*args, **kwargs)
            duration = time.perf_counter() - start
            LLM_REQUESTS.labels(model=self._model,
                                stage=self._stage, status="ok").inc()
            LLM_LATENCY.labels(model=self._model,
                               stage=self._stage).observe(duration)
            LLM_TOKENS.labels(model=self._model, stage=self._stage,
                              kind="prompt").inc(prompt_tokens)
            LLM_TOKENS.labels(
                model=self._model, stage=self._stage, kind="completion"
            ).inc(_estimate_tokens(getattr(result, "content", result)))
            return result
        except Exception:
            LLM_REQUESTS.labels(model=self._model,
                                stage=self._stage, status="error").inc()
            LLM_FALLBACKS.labels(stage=self._stage, reason="error").inc()
            raise

    async def ainvoke(self, *args, **kwargs):
        prompt_tokens = _estimate_tokens(
            args[0] if args else kwargs.get("input"))
        start = time.perf_counter()
        try:
            result = await self._inner.ainvoke(*args, **kwargs)
            duration = time.perf_counter() - start
            LLM_REQUESTS.labels(model=self._model,
                                stage=self._stage, status="ok").inc()
            LLM_LATENCY.labels(model=self._model,
                               stage=self._stage).observe(duration)
            LLM_TOKENS.labels(model=self._model, stage=self._stage,
                              kind="prompt").inc(prompt_tokens)
            LLM_TOKENS.labels(
                model=self._model, stage=self._stage, kind="completion"
            ).inc(_estimate_tokens(getattr(result, "content", result)))
            return result
        except Exception:
            LLM_REQUESTS.labels(model=self._model,
                                stage=self._stage, status="error").inc()
            LLM_FALLBACKS.labels(stage=self._stage, reason="error").inc()
            raise

    # ---- LangChain passthroughs ----
    def __or__(self, other):
        """prompt | llm must return a chain that still records metrics."""
        return _MeasuredChain(self, other)

    def with_structured_output(self, *a, **k):
        inner_structured = self._inner.with_structured_output(*a, **k)
        return MeasuredLLM(inner_structured, stage=self._stage)

    def bind_tools(self, *a, **k):
        return MeasuredLLM(self._inner.bind_tools(*a, **k), stage=self._stage)

    def __getattr__(self, name):
        # Fallback: any other attribute passes through
        return getattr(self._inner, name)


class _MeasuredChain:
    """Handles `prompt | MeasuredLLM` so `.invoke()` still records."""

    def __init__(self, llm: MeasuredLLM, other: Any):
        self._llm = llm
        self._other = other

    def invoke(self, inputs, **kw):
        prompt = self._other.invoke(inputs) if hasattr(
            self._other, "invoke") else inputs
        return self._llm.invoke(prompt, **kw)

    async def ainvoke(self, inputs, **kw):
        if hasattr(self._other, "ainvoke"):
            prompt = await self._other.ainvoke(inputs)
        elif hasattr(self._other, "invoke"):
            prompt = self._other.invoke(inputs)
        else:
            prompt = inputs
        return await self._llm.ainvoke(prompt, **kw)
