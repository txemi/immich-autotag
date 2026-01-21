from __future__ import annotations

from typing import Optional

from typeguard import typechecked

from immich_autotag.assets.albums.temporary_manager.naming import get_temporary_album_name
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def create_album_if_missing_classification(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> Optional[str]:
    """
    Creates and assigns a temporary album for assets with no classification album.

    Conditions:
    - Feature flag `create_album_from_date_if_missing` must be enabled
    - Asset must not have exclusion tags (ignore, meme, etc.)
    - Date must be extractable from asset

    Returns:
        Album name (str) if created/assigned, None if skipped or failed
    """
    # Check feature flag
    from immich_autotag.config.manager import ConfigManager

    config = ConfigManager.get_instance().config
    if not config or not config.create_album_from_date_if_missing:
        return None

    # Safety check: this function should only be called when NO classification rules matched
    # If any rule matches here, it's a logic/configuration error.
    from immich_autotag.classification.classification_rule_set import (
        ClassificationRuleSet,
    )

    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    match_results = rule_set.matching_rules(asset_wrapper)

    # Check that asset is truly unclassified
    from immich_autotag.classification.classification_status import ClassificationStatus

    status = match_results.classification_status()
    if status != ClassificationStatus.UNCLASSIFIED:
        raise RuntimeError(
            "create_album_if_missing_classification called for an already-classified asset; this should not happen."
        )

    # Extract date
    album_date = _extract_album_date(asset_wrapper)
    if not album_date:
        log(
            f"[ALBUM CREATION] Could not extract date from asset "
            f"'{asset_wrapper.original_file_name}', skipping auto-album creation.",
            level=LogLevel.ERROR,
        )
        return None

    # Generate album name using centralized pattern
    album_name = get_temporary_album_name(album_date)

    # Health check and cleanup for temporary albums before assignment
    from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album
    from immich_autotag.assets.albums.temporary_manager.health import is_temporary_album_healthy, cleanup_unhealthy_album
    albums_collection = asset_wrapper.context.albums_collection
    client = asset_wrapper.context.client
    album_wrapper = albums_collection.create_or_get_album_with_user(
        album_name, client, tag_mod_report=tag_mod_report
    )
    album = album_wrapper.album
    if is_temporary_album(album.album_name):
        if not is_temporary_album_healthy(album_wrapper):
            log(
                f"[TEMP ALBUM HEALTH] Album '{album.album_name}' is unhealthy. Deleting and recreating.",
                level=LogLevel.IMPORTANT,
            )
            cleanup_unhealthy_album(album_wrapper, client, tag_mod_report)


    # Assign asset to album using existing logic (creates if needed)
    from immich_autotag.assets.albums._process_album_detection import (
        process_album_detection,
    )

    process_album_detection(
        asset_wrapper,
        tag_mod_report,
        album_name,
        album_origin="auto-created",
    )
    return album_name


@typechecked
def _extract_album_date(asset_wrapper: AssetResponseWrapper) -> Optional[str]:
    """Extract date in YYYY-MM-DD using the asset's best date (oldest of created/file/exif)."""
    dt = asset_wrapper.get_best_date()
    return dt.strftime("%Y-%m-%d")
