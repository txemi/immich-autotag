from __future__ import annotations

from typeguard import typechecked

from immich_autotag.config.internal_config import MAX_WORKERS, USE_THREADPOOL
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug


@typechecked
def log_execution_parameters() -> None:
    log_debug(
        f"[BUG] Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}..."
    )
    log(
        f"Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}...",
        level=LogLevel.PROGRESS,
    )
