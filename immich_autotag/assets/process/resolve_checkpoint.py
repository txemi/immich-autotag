from __future__ import annotations

from typeguard import typechecked

from immich_autotag.config.user import ENABLE_CHECKPOINT_RESUME
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def resolve_checkpoint() -> tuple[str | None, int]:
    if ENABLE_CHECKPOINT_RESUME:
        stats = StatisticsManager.get_instance().load_latest()
        if stats:
            last_processed_id, skip_n = stats.last_processed_id, stats.count
        else:
            last_processed_id, skip_n = None, 0
        OVERLAP = 100
        if skip_n > 0:
            adjusted_skip_n = max(0, skip_n - OVERLAP)
            if adjusted_skip_n != skip_n:
                log(
                    f"[CHECKPOINT] Overlapping: skip_n adjusted from {skip_n} to {adjusted_skip_n} (overlap {OVERLAP})",
                    level=LogLevel.PROGRESS,
                )
            else:
                log(
                    f"[CHECKPOINT] Will skip {skip_n} assets (from checkpoint: id={last_processed_id}).",
                    level=LogLevel.PROGRESS,
                )
            skip_n = adjusted_skip_n
        else:
            log(
                f"[CHECKPOINT] Will skip {skip_n} assets (from checkpoint: id={last_processed_id}).",
                level=LogLevel.PROGRESS,
            )
    else:
        last_processed_id, skip_n = None, 0
        log(
            "[CHECKPOINT] Checkpoint resume is disabled. Starting from the beginning.",
            level=LogLevel.PROGRESS,
        )
    return last_processed_id, skip_n
