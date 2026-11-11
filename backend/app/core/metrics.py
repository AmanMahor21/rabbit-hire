# backend/app/core/metrics.py
"""
Central Prometheus metrics for Rabbit Hire.

Why one file: so every module imports the SAME metric object.
If you define `Counter("llm_requests_total", ...)` twice, Prometheus
raises a duplicate-timeseries error and /metrics 500s.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# ─────────────────────────────────────────────────────────────
# LLM metrics
# ─────────────────────────────────────────────────────────────
LLM_REQUESTS = Counter(
    "llm_requests_total",
    "Total LLM invocations",
    ["model", "stage", "status"],  # status = ok | error | fallback
)

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM call latency",
    ["model", "stage"],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60),
)

LLM_TOKENS = Counter(
    "llm_tokens_total",
    "Approximate LLM tokens consumed",
    ["model", "stage", "kind"],  # kind = prompt | completion
)

LLM_FALLBACKS = Counter(
    "llm_fallbacks_total",
    "Times code fell back to non-LLM path",
    ["stage", "reason"],  # reason = timeout | error | no_config
)

# ─────────────────────────────────────────────────────────────
# Celery / async task metrics
# ─────────────────────────────────────────────────────────────
CELERY_TASKS = Counter(
    "celery_tasks_total",
    "Celery task outcomes",
    ["task", "status"],  # status = success | failure
)

CELERY_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Celery task execution time",
    ["task"],
    buckets=(0.5, 1, 5, 15, 30, 60, 120, 300),
)

CELERY_QUEUE_LENGTH = Gauge(
    "celery_queue_length",
    "Approximate number of pending tasks (updated on scrape-friendly cadence)",
)

# ─────────────────────────────────────────────────────────────
# Retrieval / RAG metrics
# ─────────────────────────────────────────────────────────────
SEARCH_REQUESTS = Counter(
    "search_requests_total",
    "Search calls",
    ["mode"],  # mode = hybrid | filter_only | soft_retry
)

SEARCH_EMPTY = Counter(
    "search_empty_results_total",
    "Searches that returned zero results",
    ["filters_present"],  # true | false
)

SEARCH_LATENCY = Histogram(
    "search_latency_seconds",
    "Search latency",
    ["mode"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

RERANK_FALLBACKS = Counter(
    "rerank_fallbacks_total",
    "Times reranker was unavailable and vector score was used",
)

INGEST_FILES = Counter(
    "ingest_files_total",
    "Files ingested",
    ["status"],  # status = skipped | processed | failed
)
