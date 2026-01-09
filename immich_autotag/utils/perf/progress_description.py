from __future__ import annotations

import time
from typing import Optional

from typeguard import typechecked

from immich_autotag.utils.perf.performance_tracker import PerformanceTracker


@typechecked
def get_progress_description_from_perf_tracker(
    perf_tracker: Optional[PerformanceTracker], current_count: int = 0
) -> str:
    """
    Returns a textual description of current progress, including percentage and time estimation if available.
    perf_tracker: PerformanceTracker with the necessary attributes.
    current_count: number of processed elements (optional, default 0)
    """
    if perf_tracker is None:
        return "Progress not available: PerformanceTracker not initialized."
    elapsed = time.time() - perf_tracker.start_time
    from immich_autotag.utils.perf.print_perf import format_perf_progress

    return format_perf_progress(
        count=current_count,
        elapsed=elapsed,
        total_to_process=perf_tracker.total_to_process,
        estimator=perf_tracker.estimator,
        skip_n=perf_tracker.skip_n,
        total_assets=perf_tracker.total_assets,
        estimation_mode=perf_tracker.estimation_mode,
    )
