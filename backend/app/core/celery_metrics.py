# backend/app/core/celery_metrics.py
"""
Decorator that measures Celery tasks + updates queue length gauge.
"""
from __future__ import annotations

import functools
import time
from typing import Callable

from app.core.metrics import (
    CELERY_DURATION,
    CELERY_QUEUE_LENGTH,
    CELERY_TASKS,
)


def measured_task(fn: Callable) -> Callable:
    """Wrap a Celery task body. Reads broker queue length on each tick."""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        # Update queue length gauge from Celery's own inspector
        try:
            insp = self.app.control.inspect(timeout=1.0)
            active = insp.active() or {}
            reserved = insp.reserved() or {}
            total = sum(len(v) for v in active.values()) + sum(
                len(v) for v in reserved.values()
            )
            CELERY_QUEUE_LENGTH.set(total)
        except Exception:
            pass

        start = time.perf_counter()
        try:
            result = fn(self, *args, **kwargs)
            CELERY_TASKS.labels(task=fn.__name__, status="success").inc()
            return result
        except Exception:
            CELERY_TASKS.labels(task=fn.__name__, status="failure").inc()
            raise
        finally:
            CELERY_DURATION.labels(task=fn.__name__).observe(
                time.perf_counter() - start
            )

    return wrapper
