from __future__ import annotations

import time
from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.process.perf_log import perf_log
from immich_autotag.assets.process.process_single_asset import process_single_asset
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator


@typechecked
def process_assets_sequential(
    context: ImmichContext,
    max_assets: int | None,
    skip_n: int,
    last_processed_id: str | None,
    tag_mod_report: ModificationReport,
    lock: Lock,
    estimator: AdaptiveTimeEstimator,
    total_to_process: int | None,
    LOG_INTERVAL: int,
    start_time: float,
    total_assets: int | None,
) -> int:
    log(
        "Entering asset processing loop...",
        level=LogLevel.PROGRESS,
    )
    log("[DEBUG] Before iterating assets (start of for loop)", level=LogLevel.DEBUG)
    count = 0
    last_log_time = time.time()
    try:
        for asset_wrapper in context.asset_manager.iter_assets(
            context, max_assets=max_assets, skip_n=skip_n
        ):
            log_debug(
                f"[BUG] Processing asset: {getattr(asset_wrapper, 'id', asset_wrapper)}"
            )
            t0 = time.time()
            process_single_asset(asset_wrapper, tag_mod_report, lock)
            log(
                f"Iteration completed for asset: {getattr(asset_wrapper, 'id', asset_wrapper)}",
                level=LogLevel.DEBUG,
            )
            count += 1
            StatisticsManager.get_instance().update_checkpoint(
                asset_wrapper.id,
                skip_n + count,
            )
            t1 = time.time()
            estimator.update(t1 - t0)
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        log(
            f"[ERROR] Unexpected exception in main asset loop: {e}\nTraceback:\n{tb}",
            level=LogLevel.IMPORTANT,
        )
        raise
    finally:
        log("Asset processing loop finished.", level=LogLevel.PROGRESS)
        log(
            "The asset for-loop has ended (no more assets in the iterator).",
            level=LogLevel.PROGRESS,
        )
    return count
