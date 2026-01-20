from __future__ import annotations

import concurrent.futures
import time

from typeguard import typechecked

from immich_autotag.assets.process.process_single_asset import process_single_asset
from immich_autotag.config.internal_config import MAX_WORKERS
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.errors.recoverable_error import categorize_error
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def process_assets_threadpool(
    context: ImmichContext,
) -> None:
    log(
        "[CHECKPOINT] Checkpoint/resume is only supported in sequential mode. Disable USE_THREADPOOL for this feature.",
        level=LogLevel.PROGRESS,
    )
    LOG_INTERVAL = 5  # seconds
    stats = StatisticsManager.get_instance().get_stats()
    total_to_process = stats.get_total_to_process()
    max_assets = stats.max_assets
    start_time = stats.started_at.timestamp() if stats.started_at else time.time()
    count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for asset_wrapper in context.asset_manager.iter_assets(
            context, max_assets=max_assets
        ):
            t0 = time.time()
            future = executor.submit(process_single_asset, asset_wrapper)
            futures.append(future)
            count += 1
            # Update count and checkpoint in StatisticsManager, which handles progress logging
            StatisticsManager.get_instance().update_checkpoint(asset_wrapper.id, count)
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                # Categorize the error
                categorized = categorize_error(e)
                is_recoverable = categorized.is_recoverable
                category = categorized.category_name

                if is_recoverable:
                    # Log warning but continue
                    import traceback

                    tb = traceback.format_exc()
                    log(
                        f"[WARN] {category} - Asset processing failed (skipping): {e}\nTraceback:\n{tb}",
                        level=LogLevel.IMPORTANT,
                    )

                    # Register the error in modification report
                    from immich_autotag.tags.modification_kind import ModificationKind

                    tag_mod_report = ModificationReport.get_instance()
                    if tag_mod_report:
                        tag_mod_report.add_error_modification(
                            kind=ModificationKind.ERROR_ASSET_SKIPPED_RECOVERABLE,
                            error_message=str(e),
                            error_category=category,
                            extra={"traceback": tb},
                        )
                else:
                    # Fatal error - abort the threadpool
                    import traceback

                    tb = traceback.format_exc()
                    log(
                        f"[ERROR] {category} - Aborting threadpool: {e}\nTraceback:\n{tb}",
                        level=LogLevel.IMPORTANT,
                    )
                    executor.shutdown(wait=False)
                    raise
