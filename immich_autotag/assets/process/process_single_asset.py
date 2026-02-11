from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums.analyze_and_assign_album import (
    AlbumAssignmentReport,
)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.classification_validation_result import (
    ClassificationValidationResult,
)
from immich_autotag.assets.consistency_checks._album_date_consistency import (
    check_album_date_consistency,
)
from immich_autotag.assets.date_correction.core_logic import (
    AssetDateCorrector,
)
from immich_autotag.assets.duplicate_tag_logic import (
    DuplicateTagAnalysisReport,
    analyze_duplicate_classification_tags,
)
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
    duplicate_processing = config.duplicate_processing
    if duplicate_processing is None:
        raise ValueError("duplicate_processing configuration must not be None")
    if duplicate_processing.date_correction.enabled:
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
    """Analyze and assign the asset to an album if needed.

    Returns the result of analyze_and_assign_album.
    """
    log("[DEBUG] Analyzing and assigning album...", level=LogLevel.FOCUS)
    return AlbumAssignmentReport.analyze(asset_wrapper, tag_mod_report)


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
) -> None:
    """Process a single asset through all analysis and tagging phases.

    Applies tag conversions, corrects date if enabled, analyzes duplicates,
    assigns album, validates classification, flushes the report, and updates
    tag counters. Thread-safe for report flushing.
    """

    from typing import Optional

    asset_id: Optional[AssetUUID] = asset_wrapper.get_uuid()

    log_debug(f"[BUG] START process_single_asset {asset_id}")

    asset_url = asset_wrapper.get_immich_photo_url().geturl()
    asset_name = asset_wrapper.get_original_file_name() or "[no name]"
    log(
        f"Processing asset: {asset_url} | Name: {asset_name}",
        level=LogLevel.ASSET_SUMMARY,
    )

    # Execute each phase and store results in the typed report
    from immich_autotag.assets.process.asset_process_report import AssetProcessReport

    report = AssetProcessReport(asset_wrapper=asset_wrapper)
    result_01_tag_conversion = _apply_tag_conversions(asset_wrapper)

    report.add_result(result_01_tag_conversion)
    result_02_date_correction = _correct_date_if_enabled(asset_wrapper)

    report.add_result(result_02_date_correction)
    result_03_duplicate_tag_analysis = _analyze_duplicate_tags(asset_wrapper)

    report.add_result(result_03_duplicate_tag_analysis)
    tag_mod_report = ModificationReport.get_instance()
    result_04_album_assignment = _analyze_and_assign_album(
        asset_wrapper, tag_mod_report
    )
    report.add_result(result_04_album_assignment)

    result_05_validation: ClassificationValidationResult = (
        asset_wrapper.validate_and_update_classification()
    )
    report.add_result(result_05_validation)

    result_06_album_date_consistency = check_album_date_consistency(
        asset_wrapper, tag_mod_report
    )
    report.add_result(result_06_album_date_consistency)

    log(f"[PROCESS REPORT] {report.summary()}", level=LogLevel.ASSET_SUMMARY)

    tag_mod_report.flush()
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] END asset_id={asset_wrapper.get_uuid()}",
        level=LogLevel.FOCUS,
    )
    return None
