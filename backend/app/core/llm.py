# backend/app/core/llm.py
from __future__ import annotations

from typing import Any, Optional

import openai
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.llm_stub import StubLLM
from app.core.llm_metrics import MeasuredLLM


def _build_kwargs(model: str, temperature: float, streaming: bool = False) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "api_key": settings.LLM_API_KEY,
        "model": model,
        "temperature": temperature,
        "timeout": settings.LLM_TIMEOUT,
        "max_completion_tokens": settings.LLM_MAX_TOKENS,
        "streaming": streaming,
    }
    if settings.LLM_BASE_URL:
        kwargs["base_url"] = settings.LLM_BASE_URL
    return kwargs


def is_llm_configured() -> bool:
    return bool(settings.LLM_API_KEY and settings.LLM_API_KEY.strip())


def get_fast_llm(temperature=0, streaming=False, stage: str = "generic"):
    if settings.LLM_STUB:
        return StubLLM("stub-fast", temperature)
    if not is_llm_configured():
        return None
    raw = ChatOpenAI(
        **_build_kwargs(settings.LLM_FAST_MODEL, temperature, streaming))
    return MeasuredLLM(raw, stage=stage)


def get_smart_llm(temperature=0.1, streaming=False, stage: str = "generic"):
    if settings.LLM_STUB:
        return StubLLM("stub-smart", temperature)
    if not is_llm_configured():
        return None
    raw = ChatOpenAI(
        **_build_kwargs(settings.LLM_SMART_MODEL, temperature, streaming))
    return MeasuredLLM(raw, stage=stage)


def get_openai_client():
    if not is_llm_configured():
        return None
    kwargs: dict[str, Any] = {"api_key": settings.LLM_API_KEY}
    if settings.LLM_BASE_URL:
        kwargs["base_url"] = settings.LLM_BASE_URL
    return openai.OpenAI(**kwargs)
