from __future__ import annotations

import time

from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def log_final_summary() -> None:
    from immich_autotag.statistics.statistics_manager import StatisticsManager

    stats = StatisticsManager.get_instance().get_stats()
    count = stats.count
    start_time = stats.get_start_time()
    total_time = time.time() - start_time
    log(f"Total assets processed: {count}", level=LogLevel.PROGRESS)
    log(
        f"[PERF] Total time: {total_time:.2f} s. Average per asset: {total_time/count if count else 0:.3f} s",
        level=LogLevel.PROGRESS,
    )
    tag_mod_report = ModificationReport.get_instance()
    if len(tag_mod_report.modifications) > 0:
        tag_mod_report.print_summary()
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the real minimum number of assets
    if count < MIN_ASSETS:
        raise Exception(
            f"ERROR: Unexpectedly low number of assets: {count} < {MIN_ASSETS}"
        )
