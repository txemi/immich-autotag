from __future__ import annotations

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.context.immich_context import ImmichContext


def init_collections_and_context(
    client_wrapper: ImmichClientWrapper,
) -> ImmichContext:
    """
    Initializes all collections and returns the ImmichContext instance.
    """
    # No need to build collections eagerly; just ensure context singleton exists
    context = ImmichContext.get_default_instance()
    return context


def force_full_album_loading(albums_collection: AlbumCollectionWrapper) -> None:
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker
    from immich_autotag.utils.perf.stall_watchdog import report_progress_heartbeat

    report_progress_heartbeat(
        phase="full_album_loading",
        detail="starting_force_full_album_loading",
    )
    albums_collection.ensure_all_full(perf_phase_tracker=perf_phase_tracker)


# New function: apply conversions to all assets before loading tags
def apply_conversions_to_all_assets_early(context: ImmichContext) -> None:
    """
    Iterates over all assets and applies the configured conversions as early as possible,
    before tags are accessed (lazy-load).
    Skips assets on error based on fail_fast_on_asset_errors config.
    """
    from immich_autotag.config.manager import ConfigManager
    from immich_autotag.conversions.tag_conversions import TagConversions
    from immich_autotag.errors.recoverable_error import categorize_error
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.perf.stall_watchdog import report_progress_heartbeat

    tag_conversions = TagConversions.from_config_manager()
    asset_manager = context.get_asset_manager()
    config = ConfigManager.get_instance().get_config()
    fail_fast = config.performance.fail_fast_on_asset_errors

    report_progress_heartbeat(
        phase="early_conversions",
        detail="starting_apply_conversions_to_all_assets_early",
    )

    for idx, asset in enumerate(asset_manager.iter_assets(context), 1):
        asset_id = str(asset.get_id())
        report_progress_heartbeat(
            phase="early_conversions",
            detail=f"asset_index={idx}",
            processed_count=idx,
            last_processed_id=asset_id,
        )
        try:
            asset.apply_tag_conversions(tag_conversions=tag_conversions)
        except Exception as e:
            categorized = categorize_error(e)
            is_recoverable = categorized.is_recoverable
            category = categorized.category_name
            should_skip = is_recoverable or not fail_fast

            if should_skip:
                import traceback

                tb = traceback.format_exc()
                failed_asset_id = asset.get_id()
                error_prefix = "[WARN]" if is_recoverable else "[ERROR]"
                log(
                    f"{error_prefix} {category} - Skipping conversion for asset {failed_asset_id}: {e}\nTraceback:\n{tb}",
                    level=LogLevel.IMPORTANT,
                )
                continue
            else:
                # Fatal error in fail-fast mode - re-raise
                raise

    report_progress_heartbeat(
        phase="early_conversions",
        detail="finished_apply_conversions_to_all_assets_early",
    )
