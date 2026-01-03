from __future__ import annotations

import concurrent.futures
import os
from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.process_single_asset import process_single_asset
from immich_autotag.assets.checkpoint_utils import load_checkpoint, save_checkpoint, delete_checkpoint
from immich_autotag.config.internal_config import MAX_WORKERS, USE_THREADPOOL
from immich_autotag.context.immich_context import ImmichContext
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
    print(
        f"Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}..."
    )
    # Get total assets before processing
    try:
        stats = get_server_statistics.sync(client=context.client)
        total_assets = stats.photos + stats.videos
        print(
            f"[INFO] Total assets (photos + videos) reported by Immich: {total_assets}"
        )
    except Exception as e:
        print(f"[WARN] Could not get total assets from API: {e}")
        total_assets = None
    start_time = time.time()

    # print_perf now imported from helpers
    # Usage: print_perf(count, elapsed, total_assets)

    from immich_autotag.config.user import ENABLE_CHECKPOINT_RESUME

    if ENABLE_CHECKPOINT_RESUME:
        last_processed_id, skip_n = load_checkpoint()
        OVERLAP = 100
        if skip_n > 0:
            adjusted_skip_n = max(0, skip_n - OVERLAP)
            if adjusted_skip_n != skip_n:
                print(
                    f"[CHECKPOINT] Overlapping: skip_n adjusted from {skip_n} to {adjusted_skip_n} (overlap {OVERLAP})"
                )
            else:
                print(
                    f"[CHECKPOINT] Will skip {skip_n} assets (from checkpoint: id={last_processed_id})."
                )
            skip_n = adjusted_skip_n
        else:
            print(
                f"[CHECKPOINT] Will skip {skip_n} assets (from checkpoint: id={last_processed_id})."
            )
    else:
        last_processed_id, skip_n = None, 0
        print(
            "[CHECKPOINT] Checkpoint resume is disabled. Starting from the beginning."
        )
    total_to_process = None
    if total_assets is not None:
        total_to_process = total_assets
        if skip_n:
            total_to_process = max(1, total_assets - skip_n)

    from typeguard import typechecked

    @typechecked
    def perf_log(count: int, elapsed: float, estimator: "AdaptiveTimeEstimator") -> None:
        print_perf(
            count,
            elapsed,
            total_to_process,
            estimator,
            skip_n=skip_n if skip_n else 0,
            total_assets=total_assets,
        )

    if USE_THREADPOOL:
        print(
            "[WARN] Checkpoint/resume is only supported in sequential mode. Disable USE_THREADPOOL for this feature."
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
                    print(f"[ERROR] Asset processing failed: {e}")
    else:
        for asset_wrapper in context.asset_manager.iter_assets(
            context, max_assets=max_assets, skip_n=skip_n
        ):
            t0 = time.time()
            process_single_asset(asset_wrapper, tag_mod_report, lock)
            count += 1
            save_checkpoint(asset_wrapper.id, skip_n + count)
            t1 = time.time()
            estimator.update(t1 - t0)
            now = time.time()
            if now - last_log_time >= LOG_INTERVAL:
                elapsed = now - start_time
                perf_log(count, elapsed, estimator)
                last_log_time = now

    total_time = time.time() - start_time
    print(f"Total assets: {count}")
    print(
        f"[PERF] Tiempo total: {total_time:.2f} s. Media por asset: {total_time/count if count else 0:.3f} s"
    )
    if len(tag_mod_report.modifications) > 0:
        tag_mod_report.print_summary()
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the real minimum number of assets
    if count < MIN_ASSETS:
        raise Exception(
            f"ERROR: Unexpectedly low number of assets: {count} < {MIN_ASSETS}"
        )
    # Eliminar el checkpoint si todo termina correctamente
    from immich_autotag.assets.checkpoint_utils import delete_checkpoint
    delete_checkpoint()
