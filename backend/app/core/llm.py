# backend/app/core/llm.py
from __future__ import annotations

from typing import Any, Optional

import openai
from langchain_openai import ChatOpenAI

from app.core.config import settings


def _build_kwargs(model: str, temperature: float, streaming: bool = False) -> dict[str, Any]:
    print(settings, "mmmmmmmmmmmmmmmmm")
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


def get_fast_llm(temperature: float = 0, streaming: bool = False) -> Optional[ChatOpenAI]:
    if not is_llm_configured():
        return None
    return ChatOpenAI(**_build_kwargs(settings.LLM_FAST_MODEL, temperature, streaming))


def get_smart_llm(temperature: float = 0.1, streaming: bool = False) -> Optional[ChatOpenAI]:
    if not is_llm_configured():
        return None
    return ChatOpenAI(**_build_kwargs(settings.LLM_SMART_MODEL, temperature, streaming))


def get_openai_client():
    if not is_llm_configured():
        return None
    kwargs: dict[str, Any] = {"api_key": settings.LLM_API_KEY}
    if settings.LLM_BASE_URL:
        kwargs["base_url"] = settings.LLM_BASE_URL
    return openai.OpenAI(**kwargs)
