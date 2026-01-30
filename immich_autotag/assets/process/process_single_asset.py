from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums.analyze_and_assign_album import (
    AlbumAssignmentResult,
    analyze_and_assign_album,
)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.types.uuid_wrappers import AssetUUID
from immich_autotag.assets.consistency_checks._album_date_consistency import (
    check_album_date_consistency,
)
from immich_autotag.assets.date_correction.core_logic import DateCorrectionStepResult
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    DuplicateTagAnalysisResult,
    analyze_duplicate_classification_tags,
)
from immich_autotag.config._internal_types import ErrorHandlingMode
from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
from immich_autotag.config.manager import ConfigManager
from immich_autotag.conversions.tag_conversions import TagConversions
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def _apply_tag_conversions(asset_wrapper: AssetResponseWrapper):
    """Apply tag conversions to the asset using the current config."""
    log("[DEBUG] Applying tag conversions...", level=LogLevel.FOCUS)

    tag_conversions = TagConversions.from_config_manager()
    return asset_wrapper.apply_tag_conversions(tag_conversions=tag_conversions)


@typechecked
def _correct_date_if_enabled(
    asset_wrapper: AssetResponseWrapper,
) -> DateCorrectionStepResult | None:
    """Correct the asset date if the feature is enabled in config."""

    config = ConfigManager.get_instance().get_config_or_raise()
    if (
        config.duplicate_processing is not None
        and config.duplicate_processing.date_correction is not None
        and config.duplicate_processing.date_correction.enabled
    ):
        log("[DEBUG] Correcting asset date...", level=LogLevel.FOCUS)
        from immich_autotag.assets.date_correction.core_logic import correct_asset_date

        return correct_asset_date(asset_wrapper)


@typechecked
def _analyze_duplicate_tags(
    asset_wrapper: AssetResponseWrapper,
) -> DuplicateTagAnalysisResult:
    """Analyze duplicate classification tags for the asset."""
    log("[DEBUG] Analyzing duplicate classification tags...", level=LogLevel.FOCUS)
    return analyze_duplicate_classification_tags(asset_wrapper)


@typechecked
def _analyze_and_assign_album(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> AlbumAssignmentResult:
    """Analyze and assign the asset to an album if needed. Returns the result of analyze_and_assign_album."""
    log("[DEBUG] Analyzing and assigning album...", level=LogLevel.FOCUS)
    return analyze_and_assign_album(asset_wrapper, tag_mod_report)


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
) -> None:
    """
    Process a single asset: applies tag conversions, corrects date if enabled, analyzes duplicates,
    assigns album, validates classification, flushes the report, and updates tag counters.
    Thread-safe for report flushing.
    """

    from typing import Optional

    asset_id: Optional[AssetUUID] = asset_wrapper.get_uuid()

    log_debug(f"[BUG] START process_single_asset {asset_id}")

    log(
        f"[DEBUG] [process_single_asset] START asset_id={asset_id}",
        level=LogLevel.FOCUS,
    )

    asset_url = asset_wrapper.get_immich_photo_url().geturl()
    asset_name = asset_wrapper.get_original_file_name() or "[no name]"
    log(f"Processing asset: {asset_url} | Name: {asset_name}", level=LogLevel.FOCUS)

    # Ejecutar cada fase y almacenar resultados en el reporte tipado
    from immich_autotag.assets.process.asset_process_report import AssetProcessReport

    tag_conversion_result = _apply_tag_conversions(asset_wrapper)
    date_correction_result = _correct_date_if_enabled(asset_wrapper)
    duplicate_tag_analysis_result = _analyze_duplicate_tags(asset_wrapper)
    tag_mod_report = ModificationReport.get_instance()
    album_assignment_result = _analyze_and_assign_album(asset_wrapper, tag_mod_report)
    validate_result = asset_wrapper.validate_and_update_classification()

    log(
        f"[RESERVED] tag_conversion_result: {tag_conversion_result}",
        level=LogLevel.FOCUS,
    )
    log(
        f"[RESERVED] date_correction_result: {date_correction_result}",
        level=LogLevel.FOCUS,
    )
    log(
        f"[RESERVED] duplicate_tag_analysis_result: {duplicate_tag_analysis_result}",
        level=LogLevel.FOCUS,
    )
    log(
        f"[RESERVED] album_assignment_result: {album_assignment_result}",
        level=LogLevel.FOCUS,
    )

    report = AssetProcessReport(
        tag_conversion_result=tag_conversion_result,
        date_correction_result=date_correction_result,
        duplicate_tag_analysis_result=duplicate_tag_analysis_result,
        album_assignment_result=album_assignment_result,
        validate_result=validate_result,
    )

    log(f"[PROCESS REPORT] {report.summary()}", level=LogLevel.FOCUS)

    if DEFAULT_ERROR_MODE == ErrorHandlingMode.CRAZY_DEBUG:
        raise Exception("CRAZY_DEBUG mode active - stopping after tag conversions")
    log(f"[RESERVED] validate_result: {validate_result}", level=LogLevel.DEBUG)
    from immich_autotag.config.manager import ConfigManager

    config = ConfigManager.get_instance().get_config_or_raise()
    if config.album_date_consistency and config.album_date_consistency.enabled:
        threshold_days = config.album_date_consistency.threshold_days
        check_album_date_consistency(asset_wrapper, tag_mod_report, threshold_days)

    tag_mod_report.flush()
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] END asset_id={asset_wrapper.get_uuid()}",
        level=LogLevel.FOCUS,
    )
    return None
