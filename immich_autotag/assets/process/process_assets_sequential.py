from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.process.process_single_asset import process_single_asset
from immich_autotag.config.dev_mode import is_development_mode
from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.errors.recoverable_error import categorize_error
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager


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
    cm = ConfigManager.get_instance()
    assert isinstance(cm, ConfigManager)

    # Determine skip_n and clearly show its origin
    config_skip_n = 0
    config_resume_previous = True

    config = cm.get_config_or_raise()
    # config.skip is never None
    config_skip_n = config.skip.skip_n or 0
    config_resume_previous = config.skip.resume_previous

    # Use the centralized logic of CheckpointManager to decide and log the origin
    skip_n = (
        StatisticsManager.get_instance()
        .get_checkpoint_manager()
        .get_effective_skip_n(
            config_skip_n=config_skip_n, config_resume_previous=config_resume_previous
        )
    )
    max_assets = stats.max_assets
    count = 0
    try:
        for asset_wrapper in context.get_asset_manager().iter_assets(
            context, max_assets=max_assets, skip_n=skip_n
        ):
            asset_id = asset_wrapper.get_id()
            log_debug(f"[BUG] Processing asset: {asset_id}")

            try:
                process_single_asset(asset_wrapper)
            except Exception as e:
                # Categorize the error as recoverable or fatal
                categorized = categorize_error(e)
                is_recoverable = categorized.is_recoverable
                category = categorized.category_name

                # If recoverable, or not recoverable but we are in BATCH mode, treat the same
                if is_recoverable and not is_development_mode():
                    import traceback

                    tb = traceback.format_exc()
                    asset_id = asset_wrapper.get_id()
                    log(
                        f"[WARN] {category} - Skipping asset {asset_id}: {e}\nTraceback:\n{tb}",
                        level=LogLevel.IMPORTANT,
                    )
                    from immich_autotag.report.modification_kind import ModificationKind

                    tag_mod_report = ModificationReport.get_instance()
                    if tag_mod_report:
                        tag_mod_report.add_error_modification(
                            kind=ModificationKind.ERROR_ASSET_SKIPPED_RECOVERABLE,
                            asset_wrapper=asset_wrapper,
                            error_message=str(e),
                            error_category=category,
                            extra={"traceback": tb},
                        )
                    count += 1
                    StatisticsManager.get_instance().update_checkpoint(
                        last_processed_id=asset_wrapper.get_id(),
                        count=skip_n + count,
                    )
                    continue
                else:
                    # Fatal error - re-raise inmediatamente
                    import traceback

                    tb = traceback.format_exc()
                    asset_id = asset_wrapper.get_id()
                    log(
                        f"[ERROR] {category} - Aborting at asset {asset_id}: {e}\nTraceback:\n{tb}",
                        level=LogLevel.IMPORTANT,
                    )
                    raise

            asset_id = asset_wrapper.get_id()
            log(
                f"Iteration completed for asset: {asset_id}",
                level=LogLevel.DEBUG,
            )
            count += 1
            StatisticsManager.get_instance().update_checkpoint(
                last_processed_id=asset_wrapper.get_id(),
                count=skip_n + count,
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
