from __future__ import annotations

from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.asset_validation import validate_and_update_asset_classification
from immich_autotag.assets.albums.analyze_and_assign_album import analyze_and_assign_album
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import analyze_duplicate_classification_tags
from immich_autotag.config.user import ENABLE_DATE_CORRECTION, TAG_CONVERSIONS
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
            or "[sin nombre]"
        )
        from pprint import pformat

        details = pformat(vars(asset_wrapper))
        log(
            f"[ERROR] No se pudo obtener la URL Immich del asset. Nombre: {asset_name}\nDetalles: {details}",
            level=LogLevel.FOCUS,
        )
        raise RuntimeError(
            f"Could not obtain Immich URL for asset. Name: {asset_name}. Exception: {e}\nDetails: {details}"
        )
    asset_name = asset_wrapper.original_file_name
    if not asset_name:
        asset_name = "[sin nombre]"
    log(f"Procesando asset: {asset_url} | Nombre: {asset_name}", level=LogLevel.FOCUS)

    log("[DEBUG] Aplicando conversiones de tags...", level=LogLevel.FOCUS)
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS)

    if ENABLE_DATE_CORRECTION:
        log("[DEBUG] Corrigiendo fecha del asset...", level=LogLevel.FOCUS)
        from immich_autotag.assets.date_correction.core_logic import correct_asset_date

        correct_asset_date(asset_wrapper)

    log(
        "[DEBUG] Analizando tags de clasificación de duplicados...",
        level=LogLevel.FOCUS,
    )
    analyze_duplicate_classification_tags(asset_wrapper)

    log("[DEBUG] Analizando y asignando álbum...", level=LogLevel.FOCUS)
    analyze_and_assign_album(
        asset_wrapper, tag_mod_report, suppress_album_already_belongs_log
    )

    log(
        "[DEBUG] Validando y actualizando clasificación del asset...",
        level=LogLevel.FOCUS,
    )
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )

    log(
        "[DEBUG] Intentando adquirir lock para flush del reporte...",
        level=LogLevel.FOCUS,
    )
    with lock:
        log(
            "[DEBUG] Lock adquirido, haciendo flush del reporte...",
            level=LogLevel.FOCUS,
        )
        tag_mod_report.flush()
    # Actualiza los contadores totales de etiquetas de salida para este asset
    StatisticsManager.get_instance().process_asset_tags(asset_wrapper.get_tag_names())
    log(
        f"[DEBUG] [process_single_asset] FIN asset_id={getattr(asset_wrapper, 'id', None)}",
        level=LogLevel.FOCUS,
    )
