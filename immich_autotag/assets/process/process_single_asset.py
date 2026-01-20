from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums.analyze_and_assign_album import (
    analyze_and_assign_album,
)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    analyze_duplicate_classification_tags,
)
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def _get_asset_url(asset_wrapper: AssetResponseWrapper) -> str:
    """Get the Immich URL for the asset, raising a detailed error if it fails."""
    try:
        log("[DEBUG] Getting asset URL...", level=LogLevel.FOCUS)
        return asset_wrapper.get_immich_photo_url().geturl()
    except Exception as e:
        try:
            asset_name = asset_wrapper.original_file_name
        except AttributeError:
            asset_name = "[no name]"
        from pprint import pformat

        details = pformat(vars(asset_wrapper))
        log(
            f"[ERROR] Could not obtain the Immich URL for the asset. Name: {asset_name}\nDetails: {details}",
            level=LogLevel.FOCUS,
        )
        raise RuntimeError(
            f"Could not obtain Immich URL for asset. Name: {asset_name}. Exception: {e}\nDetails: {details}"
        )


@typechecked
def _apply_tag_conversions(asset_wrapper: AssetResponseWrapper):
    """Apply tag conversions to the asset using the current config."""
    log("[DEBUG] Applying tag conversions...", level=LogLevel.FOCUS)
    from immich_autotag.conversions.tag_conversions import TagConversions

    tag_conversions = TagConversions.from_config_manager()
    asset_wrapper.apply_tag_conversions(tag_conversions)


@typechecked
def _correct_date_if_enabled(asset_wrapper: AssetResponseWrapper):
    """Correct the asset date if the feature is enabled in config."""
    from immich_autotag.config.manager import ConfigManager

    config = ConfigManager.get_instance().config
    if (
        config is not None
        and config.duplicate_processing is not None
        and config.duplicate_processing.date_correction is not None
        and config.duplicate_processing.date_correction.enabled
    ):
        log("[DEBUG] Correcting asset date...", level=LogLevel.FOCUS)
        from immich_autotag.assets.date_correction.core_logic import correct_asset_date

        correct_asset_date(asset_wrapper)


@typechecked
def _analyze_duplicate_tags(asset_wrapper: AssetResponseWrapper):
    """Analyze duplicate classification tags for the asset."""
    log("[DEBUG] Analyzing duplicate classification tags...", level=LogLevel.FOCUS)
    analyze_duplicate_classification_tags(asset_wrapper)


@typechecked
def _analyze_and_assign_album(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
):
    """Analyze and assign the asset to an album if needed."""
    log("[DEBUG] Analyzing and assigning album...", level=LogLevel.FOCUS)
    analyze_and_assign_album(asset_wrapper, tag_mod_report)


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
) -> None:
    """
    Process a single asset: applies tag conversions, corrects date if enabled, analyzes duplicates,
    assigns album, validates classification, flushes the report, and updates tag counters.
    Thread-safe for report flushing.
    """
    try:
        asset_id = asset_wrapper.id
    except AttributeError:
        asset_id = None
    log_debug(f"[BUG] START process_single_asset {asset_id}")
    try:
        asset_id = asset_wrapper.id
    except AttributeError:
        asset_id = None
    log(
        f"[DEBUG] [process_single_asset] START asset_id={asset_id}",
        level=LogLevel.FOCUS,
    )

    asset_url = _get_asset_url(asset_wrapper)
    asset_name = asset_wrapper.original_file_name or "[no name]"
    log(f"Processing asset: {asset_url} | Name: {asset_name}", level=LogLevel.FOCUS)

    _apply_tag_conversions(asset_wrapper)
    _correct_date_if_enabled(asset_wrapper)
    _analyze_duplicate_tags(asset_wrapper)
    tag_mod_report = ModificationReport.get_instance()
    _analyze_and_assign_album(asset_wrapper, tag_mod_report)
    _ = asset_wrapper.validate_and_update_classification()
    from immich_autotag.assets.consistency_checks._album_date_consistency import (
        check_album_date_consistency,
    )
    from immich_autotag.config.manager import ConfigManager

    config = ConfigManager.get_instance().config

    # Get threshold from new config section with fallback
    if (
        config
        and config.album_date_consistency
        and config.album_date_consistency.enabled
    ):
        threshold_days = config.album_date_consistency.threshold_days
        check_album_date_consistency(asset_wrapper, tag_mod_report, threshold_days)

    tag_mod_report.flush()
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    try:
        asset_id = asset_wrapper.id
    except AttributeError:
        asset_id = None
    log(
        f"[DEBUG] [process_single_asset] END asset_id={asset_id}",
        level=LogLevel.FOCUS,
    )
