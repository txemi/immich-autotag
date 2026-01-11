from __future__ import annotations

import concurrent.futures
import time
from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.process.perf_log import perf_log
from immich_autotag.assets.process.process_single_asset import process_single_asset
from immich_autotag.config.internal_config import MAX_WORKERS
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator


@typechecked
def process_assets_threadpool(
    context: ImmichContext,
    max_assets: int | None,
    tag_mod_report: ModificationReport,
    lock: Lock,
    estimator: AdaptiveTimeEstimator,
    total_to_process: int | None,
    skip_n: int,
    total_assets: int | None,
    LOG_INTERVAL: int,
    start_time: float,
) -> None:
    log(
        "[CHECKPOINT] Checkpoint/resume is only supported in sequential mode. Disable USE_THREADPOOL for this feature.",
        level=LogLevel.PROGRESS,
    )
    count = 0
    last_log_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for asset_wrapper in context.asset_manager.iter_assets(
            context, max_assets=max_assets
        ):
            t0 = time.time()
            future = executor.submit(
                process_single_asset, asset_wrapper, tag_mod_report, lock
            )
            futures.append(future)
            t1 = time.time()
            estimator.update(t1 - t0)
            count += 1
            now = time.time()
            if now - last_log_time >= LOG_INTERVAL:
                elapsed = now - start_time
                perf_log(
                    count, elapsed, estimator, total_to_process, skip_n, total_assets
                )
                last_log_time = now
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(
                    f"[ERROR] Failed to process an asset in the threadpool: {e}",
                    level=LogLevel.IMPORTANT,
                )
