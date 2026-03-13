from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import is_log_level_enabled, log

T = TypeVar("T")


def generic_debug_operation():
    """
    Generic function for debug/proxy operations.
    Receives input and returns a debug response.
    """
    # Here would be the generic logic
    pass


def read_operation_debug():
    """
    Explicit function for read/query operations.
    Receives input and returns a read response.
    """
    # Here would be the logic for reading
    pass


def write_operation_debug():
    """
    Explicit function for write/modify operations.
    Receives input and the operation type to perform.
    """
    # Here would be the logic for modification
    pass


def api_debug_breakpoint():
    """
    Dummy function for debugging. Set a breakpoint here to catch all active API calls.
    """
    pass


def format_api_debug_context(**context: Any) -> str:
    items = [f"{key}={value}" for key, value in context.items() if value is not None]
    return " | ".join(items)


def timed_api_call(
    *,
    operation: str,
    func: Callable[[], T],
    context: str | None = None,
    slow_threshold_seconds: float = 5.0,
) -> T:
    start = time.perf_counter()
    try:
        result = func()
    except Exception as exc:
        elapsed = time.perf_counter() - start
        message = f"[HTTP-DIAG] {operation} failed after {elapsed:.3f}s"
        if context:
            message = f"{message} | {context}"
        message = f"{message} | error={exc.__class__.__name__}"
        log(message, LogLevel.IMPORTANT)
        raise

    elapsed = time.perf_counter() - start
    if elapsed >= slow_threshold_seconds:
        level = LogLevel.FOCUS
        state = "slow"
    elif is_log_level_enabled(LogLevel.DEBUG):
        level = LogLevel.DEBUG
        state = "ok"
    else:
        return result

    message = f"[HTTP-DIAG] {operation} {state} in {elapsed:.3f}s"
    if context:
        message = f"{message} | {context}"
    log(message, level)
    return result


__all__ = [
    "api_debug_breakpoint",
    "format_api_debug_context",
    "generic_debug_operation",
    "read_operation_debug",
    "timed_api_call",
    "write_operation_debug",
]
