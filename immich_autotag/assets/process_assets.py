from __future__ import annotations

import concurrent.futures
import os
from threading import Lock

from typeguard import typechecked

from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.assets.process_single_asset import process_single_asset
from immich_autotag.config.internal_config import MAX_WORKERS, USE_THREADPOOL
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.utils import log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.utils.perf.print_perf import print_perf

# --- Checkpoint helpers (moved to end for style) ---


@typechecked
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator

    estimator = AdaptiveTimeEstimator(alpha=0.05)
    import time

    from immich_client.api.server import get_server_statistics

    tag_mod_report = ModificationReport.get_instance()
    lock = Lock()
    count = 0
    LOG_INTERVAL = 5  # seconds
    last_log_time = time.time()
    log_debug(
        f"[BUG] Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}..."
    )
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log(
        f"Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}...",
        level=LogLevel.PROGRESS,
    )
    # Get total assets before processing
    try:
        stats = get_server_statistics.sync(client=context.client)
        total_assets = stats.photos + stats.videos
        log(
            f"Total assets (photos + videos) reported by Immich: {total_assets}",
            level=LogLevel.PROGRESS,
        )
        StatisticsManager.get_instance().set_total_assets(total_assets)
    except Exception as e:
        log(
            f"[ERROR] Could not get total assets from API: {e}",
            level=LogLevel.IMPORTANT,
        )
        total_assets = None
    start_time = time.time()

    # print_perf now imported from helpers
    # Usage: print_perf(count, elapsed, total_assets)

    from immich_autotag.config.user import ENABLE_CHECKPOINT_RESUME

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
    # Guardar parámetros de ejecución en estadísticas
    StatisticsManager.get_instance().set_max_assets(max_assets if max_assets is not None else -1)
    StatisticsManager.get_instance().set_skip_n(skip_n)
    total_to_process = None
    if total_assets is not None:
        total_to_process = total_assets
        if skip_n:
            total_to_process = max(1, total_assets - skip_n)

    from typeguard import typechecked

    from immich_autotag.utils.perf.time_estimation_mode import \
        TimeEstimationMode

    @typechecked
    def perf_log(
        count: int,
        elapsed: float,
        estimator: "AdaptiveTimeEstimator",
        estimation_mode: TimeEstimationMode = TimeEstimationMode.LINEAR,
    ) -> None:
        print_perf(
            count,
            elapsed,
            total_to_process,
            estimator,
            skip_n=skip_n if skip_n else 0,
            total_assets=total_assets,
            estimation_mode=estimation_mode,
        )

    if USE_THREADPOOL:
        log(
            "[CHECKPOINT] Checkpoint/resume is only supported in sequential mode. Disable USE_THREADPOOL for this feature.",
            level=LogLevel.PROGRESS,
        )
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
                    perf_log(count, elapsed, estimator)
                    last_log_time = now
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log(
                        f"[ERROR] Fallo al procesar un asset en el threadpool: {e}",
                        level=LogLevel.IMPORTANT,
                    )
    else:
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            "Entrando en el bucle de procesamiento de assets...",
            level=LogLevel.PROGRESS,
        )
        log("[DEBUG] Antes de iterar assets (inicio del for)", level=LogLevel.DEBUG)
        try:
            for asset_wrapper in context.asset_manager.iter_assets(
                context, max_assets=max_assets, skip_n=skip_n
            ):
                log_debug(
                    f"[BUG] Procesando asset: {getattr(asset_wrapper, 'id', asset_wrapper)}"
                )
                t0 = time.time()
                process_single_asset(asset_wrapper, tag_mod_report, lock)
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(
                    f"Iteración completada para asset: {getattr(asset_wrapper, 'id', asset_wrapper)}",
                    level=LogLevel.DEBUG,
                )
                count += 1
                StatisticsManager.get_instance().update_checkpoint(asset_wrapper.id, skip_n + count)
                t1 = time.time()
                estimator.update(t1 - t0)
                now = time.time()
                if now - last_log_time >= LOG_INTERVAL:
                    elapsed = now - start_time
                    perf_log(count, elapsed, estimator)
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
    # Marcar finalización de estadísticas
    StatisticsManager.get_instance().finish_run()
