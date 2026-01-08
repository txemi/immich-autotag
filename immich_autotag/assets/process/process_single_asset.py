from __future__ import annotations

from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.albums.analyze_and_assign_album import \
    analyze_and_assign_album
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import \
    analyze_duplicate_classification_tags
from immich_autotag.assets.validation.validate_and_update_asset_classification import \
    validate_and_update_asset_classification
from immich_autotag.config.user import ENABLE_DATE_CORRECTION
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    lock: Lock,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    log_debug(f"[BUG] INICIO process_single_asset {getattr(asset_wrapper, 'id', None)}")

    log(
        f"[DEBUG] [process_single_asset] INICIO asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )
    try:
        log("[DEBUG] Obteniendo URL del asset...", level=LogLevel.FOCUS)
        asset_url = asset_wrapper.get_immich_photo_url().geturl()
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
    asset_name = asset_wrapper.original_file_name
    if not asset_name:
        asset_name = "[no name]"
    log(f"Procesando asset: {asset_url} | Nombre: {asset_name}", level=LogLevel.FOCUS)

    log("[DEBUG] Aplicando conversiones de tags...", level=LogLevel.FOCUS)
    from immich_autotag.conversions.tag_conversions import TagConversions

    tag_conversions = TagConversions.from_config_manager()
    asset_wrapper.apply_tag_conversions(tag_conversions)

    if ENABLE_DATE_CORRECTION:
        log("[DEBUG] Corrigiendo fecha del asset...", level=LogLevel.FOCUS)
        from immich_autotag.assets.date_correction.core_logic import \
            correct_asset_date

        correct_asset_date(asset_wrapper)

    log(
        "[DEBUG] Analyzing duplicate classification tags...",
        level=LogLevel.FOCUS,
    )
    analyze_duplicate_classification_tags(asset_wrapper)

    log("[DEBUG] Analyzing and assigning album...", level=LogLevel.FOCUS)
    analyze_and_assign_album(
        asset_wrapper, tag_mod_report, suppress_album_already_belongs_log
    )

    log(
        "[DEBUG] Validating and updating asset classification...",
        level=LogLevel.FOCUS,
    )
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )

    log(
        "[DEBUG] Attempting to acquire lock for report flush...",
        level=LogLevel.FOCUS,
    )
    with lock:
        log(
            "[DEBUG] Lock acquired, flushing report...",
            level=LogLevel.FOCUS,
        )
        tag_mod_report.flush()
    # Update total output tag counters for this asset
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] FIN asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )
