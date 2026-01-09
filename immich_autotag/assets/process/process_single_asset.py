from __future__ import annotations

from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.albums.analyze_and_assign_album import (
    analyze_and_assign_album,
)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    analyze_duplicate_classification_tags,
)
from immich_autotag.assets.validation.validate_and_update_asset_classification import (
    validate_and_update_asset_classification,
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
        asset_name = (
            getattr(asset_wrapper, "original_file_name", None)
            or getattr(asset_wrapper, "filename", None)
            or "[no name]"
        )
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
    if config and config.features.date_correction.enabled:
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
    suppress_album_already_belongs_log: bool,
):
    """Analyze and assign the asset to an album if needed."""
    log("[DEBUG] Analyzing and assigning album...", level=LogLevel.FOCUS)
    analyze_and_assign_album(
        asset_wrapper, tag_mod_report, suppress_album_already_belongs_log
    )


@typechecked
def _validate_and_update_classification(
    asset_wrapper: AssetResponseWrapper, tag_mod_report: ModificationReport
):
    """Validate and update the asset's classification tags."""
    log("[DEBUG] Validating and updating asset classification...", level=LogLevel.FOCUS)
    validate_and_update_asset_classification(
        asset_wrapper, tag_mod_report=tag_mod_report
    )


@typechecked
def _flush_report_with_lock(lock: Lock, tag_mod_report: ModificationReport):
    """Flush the modification report, acquiring the lock for thread safety."""
    log("[DEBUG] Attempting to acquire lock for report flush...", level=LogLevel.FOCUS)
    with lock:
        log("[DEBUG] Lock acquired, flushing report...", level=LogLevel.FOCUS)
        tag_mod_report.flush()


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    lock: Lock,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    """
    Process a single asset: applies tag conversions, corrects date if enabled, analyzes duplicates,
    assigns album, validates classification, flushes the report, and updates tag counters.
    Thread-safe for report flushing.
    """
    log_debug(f"[BUG] START process_single_asset {getattr(asset_wrapper, 'id', None)}")
    log(
        f"[DEBUG] [process_single_asset] START asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )

    asset_url = _get_asset_url(asset_wrapper)
    asset_name = asset_wrapper.original_file_name or "[no name]"
    log(f"Processing asset: {asset_url} | Name: {asset_name}", level=LogLevel.FOCUS)

    _apply_tag_conversions(asset_wrapper)
    _correct_date_if_enabled(asset_wrapper)
    _analyze_duplicate_tags(asset_wrapper)
    _analyze_and_assign_album(
        asset_wrapper, tag_mod_report, suppress_album_already_belongs_log
    )

    _validate_and_update_classification(asset_wrapper, tag_mod_report)

    # Album date consistency check (after all other processing)
    from immich_autotag.assets.consistency_checks._album_date_consistency import (
        check_album_date_consistency,
    )

    check_album_date_consistency(asset_wrapper, tag_mod_report)

    _flush_report_with_lock(lock, tag_mod_report)
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] END asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )
