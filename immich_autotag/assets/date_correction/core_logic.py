from .asset_date_sources_list import AssetDateSourcesList
from .asset_date_candidates import AssetDateCandidates

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

from .asset_date_sources import AssetDateSources
def get_asset_date_sources(asset_wrapper: AssetResponseWrapper) -> AssetDateSources:
    """
    Extract all relevant date sources for a given asset.
    Returns an AssetDateSources object with immich_date, WhatsApp filename date, and WhatsApp path date.
    """
    immich_date = asset_wrapper.get_best_date()
    wa_filename_date = extract_whatsapp_date_from_path(getattr(asset_wrapper.asset, 'original_file_name', ''))
    wa_path_date = extract_whatsapp_date_from_path(getattr(asset_wrapper.asset, 'original_path', ''))
    return AssetDateSources(
        asset_id=asset_wrapper.asset.id,
        immich_date=immich_date,
        whatsapp_filename_date=wa_filename_date,
        whatsapp_path_date=wa_path_date,
    )

@typechecked
def correct_asset_date(asset_wrapper: AssetResponseWrapper) -> None:
    """
    Main entry point for asset date correction logic.
    For WhatsApp assets, finds the oldest date among Immich and filename-extracted dates from all duplicates.
    """
    # Always consider all possible date sources, even if there are no duplicates
    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    wrappers.append(asset_wrapper)
    date_sources_list = AssetDateSourcesList.from_wrappers(wrappers)
    date_candidates = AssetDateCandidates()
    date_sources_list.add_all_candidates_to(date_candidates.candidates)
    if date_candidates.is_empty():
        print(f"[DATE CORRECTION] No date candidates found for asset {asset_wrapper.asset.id}")
        return
    print("[DEBUG] Fechas candidatas y sus tipos/tzinfo:")
    for label, d in date_candidates:
        print(f"  {label}: {d!r} (type={type(d)}, tzinfo={getattr(d, 'tzinfo', None)})")
    # This will fail if there are naive and aware datetimes, but that's intentional for debugging
    oldest = date_candidates.oldest()
    # Get the Immich date (the one visible and modifiable in the UI)
    immich_date = asset_wrapper.get_best_date()
    # If Immich date is the oldest or strictly earlier than all suggestions, do nothing
    if all(immich_date <= d for _, d in date_candidates):
        print(f"[DATE CORRECTION] Immich date {immich_date} ya es la más antigua o igual a todas las sugeridas, no se hace nada.")
        return
    # If Immich date is the same day as the oldest, do nothing
    if immich_date.date() == oldest.date():
        print(f"[DATE CORRECTION] Immich date {immich_date} es del mismo día que la más antigua {oldest}, no se hace nada.")
        return
    # New: If the best candidate is less than 4h different and Immich has time info but candidate is exactly at 00:00:00, keep Immich's date
    from datetime import timedelta
    diff = abs((oldest.astimezone(ZoneInfo("UTC")) - immich_date.astimezone(ZoneInfo("UTC"))).total_seconds())
    if (
        diff < 4 * 3600
        and (immich_date.hour != 0 or immich_date.minute != 0 or immich_date.second != 0)
        and oldest.hour == 0 and oldest.minute == 0 and oldest.second == 0
    ):
        print(f"[DATE CORRECTION] Immich date {immich_date} tiene hora precisa y la sugerida {oldest} es redondeada y muy cercana (<4h). No se hace nada.")
        return
    photo_url_obj = asset_wrapper.get_immich_photo_url()
    photo_url = photo_url_obj.geturl()
    print(f"[DATE CORRECTION][LINK] Asset {asset_wrapper.asset.id} -> {photo_url}")
    # Print both dates in UTC for clarity
    def to_utc(dt):
        return dt.astimezone(ZoneInfo("UTC")) if dt.tzinfo else dt
    immich_utc = to_utc(immich_date)
    oldest_utc = to_utc(oldest)
    msg = (
        f"[DATE CORRECTION] Caso no implementado: Immich date {immich_date} y oldest {oldest} (asset {asset_wrapper.asset.id})\n"
        f"[DATE CORRECTION][UTC] Immich date UTC: {immich_utc}, oldest UTC: {oldest_utc}"
    )
    print(msg)
    raise NotImplementedError(msg)