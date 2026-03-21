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
    AlbumDateConsistencyResult,
    check_album_date_consistency,
)
from immich_autotag.assets.date_correction.core_logic import (
    AssetDateCorrector,
)
from immich_autotag.assets.duplicate_tag_logic import (
    DuplicateTagAnalysisReport,
    analyze_duplicate_classification_tags,
)
from immich_autotag.assets.process.asset_process_report import AssetProcessReport
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
    config = ConfigManager.get_instance().get_config()
    if not config.conversions.enabled:
        log(
            "[DEBUG] Tag conversions disabled by config; skipping.",
            level=LogLevel.FOCUS,
        )
        return ModificationEntriesList()

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

    config = ConfigManager.get_instance().get_config()
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
) -> DuplicateTagAnalysisReport | None:
    """Analyze duplicate classification tags for the asset."""
    from immich_autotag.config.internal_config import (
        FORCE_ENABLE_DUPLICATE_TAG_ANALYSIS,
    )

    if FORCE_ENABLE_DUPLICATE_TAG_ANALYSIS is False:
        log(
            "[DEBUG] Duplicate tag analysis disabled by internal config; skipping.",
            level=LogLevel.FOCUS,
        )
        return None

    log("[DEBUG] Analyzing duplicate classification tags...", level=LogLevel.FOCUS)
    return analyze_duplicate_classification_tags(asset_wrapper)


@typechecked
def _assign_album_if_enabled(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> AlbumAssignmentReport | None:
    """Run album assignment unless disabled in internal config."""
    from immich_autotag.config.internal_config import FORCE_ENABLE_ALBUM_ASSIGNMENT

    if FORCE_ENABLE_ALBUM_ASSIGNMENT is False:
        log(
            "[DEBUG] Album assignment disabled by internal config; skipping.",
            level=LogLevel.FOCUS,
        )
        return None

    return AlbumAssignmentReport.analyze(asset_wrapper, tag_mod_report)


@typechecked
def _validate_classification_if_enabled(
    asset_wrapper: AssetResponseWrapper,
) -> ClassificationValidationResult | None:
    """Run classification validation unless disabled in internal config."""
    from immich_autotag.config.internal_config import (
        FORCE_ENABLE_CLASSIFICATION_VALIDATION,
    )

    if FORCE_ENABLE_CLASSIFICATION_VALIDATION is False:
        log(
            "[DEBUG] Classification validation disabled by internal config; skipping.",
            level=LogLevel.FOCUS,
        )
        return None

    return asset_wrapper.validate_and_update_classification()


@typechecked
def _check_album_date_consistency_if_enabled(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> AlbumDateConsistencyResult | None:
    """Run album date consistency check unless disabled in internal config."""
    from immich_autotag.config.internal_config import (
        FORCE_ENABLE_ALBUM_DATE_CONSISTENCY,
    )

    if FORCE_ENABLE_ALBUM_DATE_CONSISTENCY is False:
        log(
            "[DEBUG] Album date consistency check disabled by internal config; skipping.",
            level=LogLevel.FOCUS,
        )
        return None

    return check_album_date_consistency(asset_wrapper, tag_mod_report)


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
) -> AssetProcessReport:
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
        level=LogLevel.FOCUS,
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
    result_04_album_assignment = _assign_album_if_enabled(
        asset_wrapper,
        tag_mod_report,
    )
    report.add_result(result_04_album_assignment)

    result_05_validation = _validate_classification_if_enabled(asset_wrapper)
    report.add_result(result_05_validation)

    result_06_album_date_consistency = _check_album_date_consistency_if_enabled(
        asset_wrapper, tag_mod_report
    )
    report.add_result(result_06_album_date_consistency)

    log(f"[PROCESS REPORT] {report.summary()}", level=LogLevel.ASSET_SUMMARY)

    tag_mod_report.flush()
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] END asset_url={asset_url}",
        level=LogLevel.FOCUS,
    )
    return report
