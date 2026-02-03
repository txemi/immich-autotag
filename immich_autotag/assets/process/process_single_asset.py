from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums.analyze_and_assign_album import (
    AlbumAssignmentReport,
    analyze_and_assign_album,
)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.classification_validation_result import (
    ClassificationValidationResult,
)
from immich_autotag.assets.consistency_checks._album_date_consistency import (
    check_album_date_consistency,
)
from immich_autotag.assets.date_correction.core_logic import AssetDateCorrector
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    DuplicateTagAnalysisReport,
    analyze_duplicate_classification_tags,
)
from immich_autotag.config.dev_mode import is_crazy_debug_mode
from immich_autotag.config.manager import ConfigManager
from immich_autotag.conversions.tag_conversions import TagConversions
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.types.uuid_wrappers import AssetUUID


@typechecked
def _apply_tag_conversions(
    asset_wrapper: AssetResponseWrapper,
) -> ModificationEntriesList:
    """Apply tag conversions to the asset using the current config."""
    log("[DEBUG] Applying tag conversions...", level=LogLevel.FOCUS)

    tag_conversions = TagConversions.from_config_manager()
    return asset_wrapper.apply_tag_conversions(tag_conversions=tag_conversions)


@typechecked
def _correct_date_if_enabled(
    asset_wrapper: AssetResponseWrapper,
) -> AssetDateCorrector | None:
    """Correct the asset date if the feature is enabled in config.

    Returns the AssetDateCorrector instance so that diagnostic information
    can be accessed at the upper level (format_diagnosis, get_reasoning, etc.)
    """

    config = ConfigManager.get_instance().get_config_or_raise()
    if config.duplicate_processing is None:
        raise ValueError("duplicate_processing configuration must not be None")
    if config.duplicate_processing.date_correction.enabled:
        log("[DEBUG] Correcting asset date...", level=LogLevel.FOCUS)
        corrector = AssetDateCorrector(asset_wrapper=asset_wrapper)
        corrector.execute()
        return corrector
    return None


@typechecked
def _analyze_duplicate_tags(
    asset_wrapper: AssetResponseWrapper,
) -> DuplicateTagAnalysisReport:
    """Analyze duplicate classification tags for the asset."""
    log("[DEBUG] Analyzing duplicate classification tags...", level=LogLevel.FOCUS)
    return analyze_duplicate_classification_tags(asset_wrapper)


@typechecked
def _analyze_and_assign_album(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> AlbumAssignmentReport:
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
        level=LogLevel.ASSET_SUMMARY,
    )

    asset_url = asset_wrapper.get_immich_photo_url().geturl()
    asset_name = asset_wrapper.get_original_file_name() or "[no name]"
    log(
        f"Processing asset: {asset_url} | Name: {asset_name}",
        level=LogLevel.ASSET_SUMMARY,
    )

    # Ejecutar cada fase y almacenar resultados en el reporte tipado
    from immich_autotag.assets.process.asset_process_report import AssetProcessReport

    # Initialize variables before conditional to avoid UnboundLocalError
    tag_conversion_result = ModificationEntriesList()
    date_correction_result = None
    duplicate_tag_analysis_result = None
    album_assignment_result = None
    tag_mod_report = None

    tag_conversion_result = _apply_tag_conversions(asset_wrapper)
    date_correction_result = _correct_date_if_enabled(asset_wrapper)
    duplicate_tag_analysis_result = _analyze_duplicate_tags(asset_wrapper)
    tag_mod_report = ModificationReport.get_instance()
    album_assignment_result = _analyze_and_assign_album(
        asset_wrapper, tag_mod_report
    )
    validation_result: ClassificationValidationResult = (
        asset_wrapper.validate_and_update_classification()
    )

    log(
        f"[RESERVED] tag_conversion_result: {tag_conversion_result}",
        level=LogLevel.ASSET_SUMMARY,
    )
    log(
        f"[RESERVED] date_correction_result: {date_correction_result}",
        level=LogLevel.ASSET_SUMMARY,
    )
    log(
        f"[RESERVED] duplicate_tag_analysis_result: {duplicate_tag_analysis_result}",
        level=LogLevel.ASSET_SUMMARY,
    )
    if album_assignment_result is not None:
        log(
            f"[RESERVED] album_assignment_result: {album_assignment_result.format()}",
            level=LogLevel.ASSET_SUMMARY,
        )

    log(
        f"[RESERVED] validate_result: {validation_result}", level=LogLevel.ASSET_SUMMARY
    )

    if tag_mod_report is None:
        tag_mod_report = ModificationReport.get_instance()

    album_date_consistency_result = check_album_date_consistency(
        asset_wrapper, tag_mod_report
    )
    log(
        f"[RESERVED] album_date_consistency_result: {album_date_consistency_result.format()}",
        level=LogLevel.ASSET_SUMMARY,
    )

    report = AssetProcessReport(
        asset_wrapper=asset_wrapper,
        tag_conversion_result=tag_conversion_result,
        date_correction_result=date_correction_result,
        duplicate_tag_analysis_result=duplicate_tag_analysis_result,
        album_date_consistency_result=album_date_consistency_result,
        album_assignment_result=album_assignment_result,
        validate_result=validation_result,
    )

    log(f"[PROCESS REPORT] {report.summary()}", level=LogLevel.ASSET_SUMMARY)

    tag_mod_report.flush()
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] END asset_id={asset_wrapper.get_uuid()}",
        level=LogLevel.ASSET_SUMMARY,
    )
    return None
