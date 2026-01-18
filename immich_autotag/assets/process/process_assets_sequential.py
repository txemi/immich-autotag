from __future__ import annotations

import time
from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.process.perf_log import perf_log
from immich_autotag.assets.process.process_single_asset import process_single_asset
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.errors.recoverable_error import categorize_error
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport

from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.config.manager import ConfigManager


@typechecked
def process_assets_sequential(
    context: ImmichContext,
) -> int:
    log(
        "Entering asset processing loop...",
        level=LogLevel.PROGRESS,
    )
    log("[DEBUG] Before iterating assets (start of for loop)", level=LogLevel.DEBUG)
    stats = StatisticsManager.get_instance().get_stats()
    cm=ConfigManager.get_instance()
    assert isinstance(cm, ConfigManager)
    skip_n=cm.config.skip.skip_n
    max_assets = stats.max_assets
    count = 0
    try:
        for asset_wrapper in context.asset_manager.iter_assets(
            context, max_assets=max_assets, skip_n=skip_n
        ):
            log_debug(
                f"[BUG] Processing asset: {getattr(asset_wrapper, 'id', asset_wrapper)}"
            )
            t0 = time.time()

            try:
                process_single_asset(asset_wrapper)
            except Exception as e:
                # Categorize the error as recoverable or fatal
                is_recoverable, category = categorize_error(e)

                if is_recoverable:
                    # Log warning and continue to next asset
                    import traceback

                    tb = traceback.format_exc()
                    log(
                        f"[WARN] {category} - Skipping asset {getattr(asset_wrapper, 'id', '?')}: {e}\nTraceback:\n{tb}",
                        level=LogLevel.IMPORTANT,
                    )

                    # Register the error in modification report
                    from immich_autotag.tags.modification_kind import ModificationKind

                    tag_mod_report = ModificationReport.get_instance()
                    if tag_mod_report:
                        tag_mod_report.add_error_modification(
                            kind=ModificationKind.ERROR_ASSET_SKIPPED_RECOVERABLE,
                            asset_wrapper=asset_wrapper,
                            error_message=str(e),
                            error_category=category,
                            extra={"traceback": tb},
                        )

                    # Update checkpoint and continue
                    count += 1
                    StatisticsManager.get_instance().update_checkpoint(
                        asset_wrapper.id,
                        skip_n + count,
                    )
                    continue
                else:
                    # Fatal error - re-raise immediately
                    import traceback

                    tb = traceback.format_exc()
                    log(
                        f"[ERROR] {category} - Aborting at asset {getattr(asset_wrapper, 'id', '?')}: {e}\nTraceback:\n{tb}",
                        level=LogLevel.IMPORTANT,
                    )
                    raise

            log(
                f"Iteration completed for asset: {getattr(asset_wrapper, 'id', asset_wrapper)}",
                level=LogLevel.DEBUG,
            )
            count += 1
            StatisticsManager.get_instance().update_checkpoint(
                asset_wrapper.id,
                skip_n + count,
            )
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
