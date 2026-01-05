from __future__ import annotations

import concurrent.futures
import os
import time
from threading import Lock

from immich_client.api.server import get_server_statistics
from typeguard import typechecked

from immich_autotag.assets.process_single_asset import process_single_asset
from immich_autotag.config.internal_config import MAX_WORKERS, USE_THREADPOOL
from immich_autotag.config.user import ENABLE_CHECKPOINT_RESUME
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
from immich_autotag.utils.perf.print_perf import print_perf
from immich_autotag.utils.perf.time_estimation_mode import TimeEstimationMode

# --- Checkpoint helpers (moved to end for style) ---



@typechecked
def log_execution_parameters() -> None:
    log_debug(
        f"[BUG] Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}..."
    )
    log(
        f"Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}...",
        level=LogLevel.PROGRESS,
    )


@typechecked
def fetch_total_assets(context: ImmichContext) -> int | None:
    try:
        stats = get_server_statistics.sync(client=context.client)
        total_assets = stats.photos + stats.videos
        log(
            f"Total assets (photos + videos) reported by Immich: {total_assets}",
            level=LogLevel.PROGRESS,
        )
        StatisticsManager.get_instance().set_total_assets(total_assets)
        return total_assets
    except Exception as e:
        log(
            f"[ERROR] Could not get total assets from API: {e}",
            level=LogLevel.IMPORTANT,
        )
        return None


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


@typechecked
def register_execution_parameters(
    total_assets: int | None, max_assets: int | None, skip_n: int
) -> None:
    StatisticsManager.get_instance().set_max_assets(
        max_assets if max_assets is not None else -1
    )
    StatisticsManager.get_instance().set_skip_n(skip_n)


@typechecked
def perf_log(
    count: int,
    elapsed: float,
    estimator: AdaptiveTimeEstimator,
    total_to_process: int | None,
    skip_n: int,
    total_assets: int | None,
) -> None:
    print_perf(
        count,
        elapsed,
        total_to_process,
        estimator,
        skip_n=skip_n if skip_n else 0,
        total_assets=total_assets,
        estimation_mode=TimeEstimationMode.LINEAR,
    )


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
                    f"[ERROR] Fallo al procesar un asset en el threadpool: {e}",
                    level=LogLevel.IMPORTANT,
                )


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
        "Entrando en el bucle de procesamiento de assets...",
        level=LogLevel.PROGRESS,
    )
    log("[DEBUG] Antes de iterar assets (inicio del for)", level=LogLevel.DEBUG)
    count = 0
    last_log_time = time.time()
    try:
        for asset_wrapper in context.asset_manager.iter_assets(
            context, max_assets=max_assets, skip_n=skip_n
        ):
            log_debug(
                f"[BUG] Procesando asset: {getattr(asset_wrapper, 'id', asset_wrapper)}"
            )
            t0 = time.time()
            process_single_asset(asset_wrapper, tag_mod_report, lock)
            log(
                f"Iteración completada para asset: {getattr(asset_wrapper, 'id', asset_wrapper)}",
                level=LogLevel.DEBUG,
            )
            count += 1
            StatisticsManager.get_instance().update_checkpoint(
                asset_wrapper.id, skip_n + count
            )
            t1 = time.time()
            estimator.update(t1 - t0)
            now = time.time()
            if now - last_log_time >= LOG_INTERVAL:
                elapsed = now - start_time
                perf_log(
                    count, elapsed, estimator, total_to_process, skip_n, total_assets
                )
                last_log_time = now
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


@typechecked
def log_final_summary(
    count: int, tag_mod_report: ModificationReport, start_time: float
) -> None:
    total_time = time.time() - start_time
    log(f"Total assets processed: {count}", level=LogLevel.PROGRESS)
    log(
        f"[PERF] Total time: {total_time:.2f} s. Average per asset: {total_time/count if count else 0:.3f} s",
        level=LogLevel.PROGRESS,
    )
    if len(tag_mod_report.modifications) > 0:
        tag_mod_report.print_summary()
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the real minimum number of assets
    if count < MIN_ASSETS:
        raise Exception(
            f"ERROR: Unexpectedly low number of assets: {count} < {MIN_ASSETS}"
        )


@typechecked
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    estimator = AdaptiveTimeEstimator(alpha=0.05)
    tag_mod_report = ModificationReport.get_instance()
    lock = Lock()
    LOG_INTERVAL = 5  # seconds
    start_time = time.time()

    log_execution_parameters()
    total_assets = fetch_total_assets(context)
    last_processed_id, skip_n = resolve_checkpoint()
    register_execution_parameters(total_assets, max_assets, skip_n)
    total_to_process = None
    if total_assets is not None:
        total_to_process = total_assets
        if skip_n:
            total_to_process = max(1, total_assets - skip_n)

    if USE_THREADPOOL:
        process_assets_threadpool(
            context,
            max_assets,
            tag_mod_report,
            lock,
            estimator,
            total_to_process,
            skip_n,
            total_assets,
            LOG_INTERVAL,
            start_time,
        )
        # No checkpoint update in threadpool mode, so count is not tracked here
        count = None
    else:
        count = process_assets_sequential(
            context,
            max_assets,
            skip_n,
            last_processed_id,
            tag_mod_report,
            lock,
            estimator,
            total_to_process,
            LOG_INTERVAL,
            start_time,
            total_assets,
        )
    log_final_summary(count if count is not None else 0, tag_mod_report, start_time)
    # Marcar finalización de estadísticas
    StatisticsManager.get_instance().finish_run()
