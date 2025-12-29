from zoneinfo import ZoneInfo
from immich_autotag.config.user import DATE_EXTRACTION_TIMEZONE

from immich_client.api.assets import update_asset
from immich_client.models.update_asset_dto import UpdateAssetDto

import re
from datetime import datetime
from typing import Optional, List
from typeguard import typechecked

@typechecked
def extract_whatsapp_date_from_path(path: str) -> Optional[datetime]:
    """
    Try to extract a date from WhatsApp-style filenames or paths.
    Supports patterns like:
      - IMG-YYYYMMDD-WAxxxx.jpg
      - VID-YYYYMMDD-WAxxxx.mp4
      - WhatsApp Image YYYY-MM-DD at HH.MM.SS.jpeg
      - WhatsApp Video YYYY-MM-DD at HH.MM.SS.mp4
    Returns a datetime if found, else None.

    ---
    # Historial de casos reales que han motivado cambios en la función:
    - 'VID-20251229-WA0004.mp4'  # Caso real: no detectado inicialmente, añadido soporte robusto para este patrón
    ---
    """
    # Pattern 1: IMG-YYYYMMDD-WAxxxx or VID-YYYYMMDD-WAxxxx (más robusto)
    # Permite guiones, subrayados, espacios, y extensiones
    m = re.search(r"(?:IMG|VID)[-_]?(\d{4})(\d{2})(\d{2})-WA\d+", str(path), re.IGNORECASE)
    if m:
        try:
            tz = ZoneInfo(DATE_EXTRACTION_TIMEZONE)
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz)
        except Exception:
            return None
    # Pattern 2: WhatsApp Image YYYY-MM-DD at HH.MM.SS
    m = re.search(r"WhatsApp (?:Image|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{2})\.(\d{2})\.(\d{2})", str(path))
    if m:
        try:
            tz = ZoneInfo(DATE_EXTRACTION_TIMEZONE)
            return datetime(
                int(m.group(1)), int(m.group(2)), int(m.group(3)),
                int(m.group(4)), int(m.group(5)), int(m.group(6)),
                tzinfo=tz
            )
        except Exception:
            return None
    return None

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

@typechecked
def correct_asset_date(asset_wrapper: AssetResponseWrapper) -> None:
    """
    Main entry point for asset date correction logic.
    For WhatsApp assets, finds the oldest date among Immich and filename-extracted dates from all duplicates.
    """
    # Get all duplicate wrappers (including self)
    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    if not wrappers:
        return
    # Collect all dates
    date_candidates: List[datetime] = []
    for w in wrappers:
        # 1. Date from Immich
        immich_date = w.asset.created_at
        if isinstance(immich_date, datetime):
            date_candidates.append(immich_date)
        # 2. Date from WhatsApp filename
        wa_date = extract_whatsapp_date_from_path(w.asset.original_file_name)
        if wa_date:
            date_candidates.append(wa_date)
        # 3. Optionally, try from full path if available
        if hasattr(w.asset, 'original_path'):
            wa_date2 = extract_whatsapp_date_from_path(getattr(w.asset, 'original_path', ''))
            if wa_date2:
                date_candidates.append(wa_date2)
    if not date_candidates:
        return
    # Pick the oldest date
    oldest = min(date_candidates)
    # Compare with asset_wrapper.asset.created_at and update if needed
    print(f"[DATE CORRECTION] Asset {asset_wrapper.asset.id}: candidate dates = {date_candidates}, oldest = {oldest}")
    # Si la fecha más antigua es distinta, actualiza en Immich
    current_date = asset_wrapper.asset.created_at
    # Acepta tanto datetime como string en current_date
    if isinstance(current_date, str):
        try:
            from dateutil.parser import parse as parse_date
            current_date_dt = parse_date(current_date)
        except Exception:
            current_date_dt = None
    else:
        current_date_dt = current_date
    if current_date_dt != oldest:
        print(f"[DATE CORRECTION] Updating asset {asset_wrapper.asset.id} date from {current_date_dt} to {oldest}")
        # Formato ISO 8601 para Immich
        iso_date = oldest.isoformat()
        dto = UpdateAssetDto(date_time_original=iso_date)
        updated = update_asset.sync(id=asset_wrapper.asset.id, client=asset_wrapper.context.client, body=dto)
        print(f"[DATE CORRECTION] Update result: {updated}")


@typechecked
def correct_asset_date(asset_wrapper: AssetResponseWrapper) -> None:
    """
    Main entry point for asset date correction logic.
    For WhatsApp assets, finds the oldest date among Immich and filename-extracted dates from all duplicates.
    """
    # Get all duplicate wrappers (including self)
    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    if not wrappers:
        return
    # Collect all dates
    date_candidates: List[tuple[str, datetime]] = []
    for w in wrappers:
        # 1. Date from Immich
        immich_date = w.get_best_date()
        date_candidates.append((f"immich_date {w.asset.id}", immich_date))
        # 2. Date from WhatsApp filename
        wa_date = extract_whatsapp_date_from_path(w.asset.original_file_name)
        if wa_date:
            date_candidates.append((f"wa_date {w.asset.id}", wa_date))
        # 3. Optionally, try from full path if available
        wa_date2 = extract_whatsapp_date_from_path(w.asset.original_path)
        if wa_date2:
            date_candidates.append((f"wa_date2 {w.asset.id}", wa_date2))
    if not date_candidates:
        return
    print("[DEBUG] Fechas candidatas y sus tipos/tzinfo:")
    for label, d in date_candidates:
        print(f"  {label}: {d!r} (type={type(d)}, tzinfo={getattr(d, 'tzinfo', None)})")
    # Esto va a fallar si hay naive y aware, pero así vemos el problema
    oldest = min([d for _, d in date_candidates])
    # Obtener la fecha de Immich (la que se ve y se puede modificar en la UI)
    immich_date = asset_wrapper.get_best_date()
    # Si la fecha de Immich ya es la más antigua, no hacer nada
    if immich_date == oldest:
        print(f"[DATE CORRECTION] Immich date {immich_date} ya es la más antigua, no se hace nada.")
        return
    # Si la fecha de Immich es del mismo día que la más antigua (ignorando hora), tampoco hacer nada
    if immich_date.date() == oldest.date():
        print(f"[DATE CORRECTION] Immich date {immich_date} es del mismo día que la más antigua {oldest}, no se hace nada.")
        return
    # En cualquier otro caso, imprimir enlace a la foto y lanzar excepción para revisión futura
    photo_url_obj = asset_wrapper.get_immich_photo_url()
    if not photo_url_obj:
        raise RuntimeError(f"No se pudo obtener la URL de Immich para el asset {asset_wrapper.asset.id}")
    photo_url = photo_url_obj.geturl()
    print(f"[DATE CORRECTION][LINK] Asset {asset_wrapper.asset.id} -> {photo_url}")
    raise NotImplementedError(f"[DATE CORRECTION] Caso no implementado: Immich date {immich_date} y oldest {oldest} (asset {asset_wrapper.asset.id})")
    if current_date_dt != oldest:
        print(f"[DATE CORRECTION] Updating asset {asset_wrapper.asset.id} date from {current_date_dt} to {oldest}")
        # Formato ISO 8601 para Immich
        iso_date = oldest.isoformat()
        dto = UpdateAssetDto(date_time_original=iso_date)
        updated = update_asset.sync(id=asset_wrapper.asset.id, client=asset_wrapper.context.client, body=dto)
        print(f"[DATE CORRECTION] Update result: {updated}")        