from .asset_date_sources_list import AssetDateSourcesList
from .asset_date_candidates import AssetDateCandidates

from zoneinfo import ZoneInfo
from immich_autotag.config.user import DATE_EXTRACTION_TIMEZONE

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


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
    date_candidates = date_sources_list.to_candidates()
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
    # Si la fecha de Immich es la más antigua o igual a todas las sugeridas, no se hace nada
    if date_candidates.immich_date_is_oldest_or_equal(immich_date):
        print(f"[DATE CORRECTION] Immich date {immich_date} ya es la más antigua o igual a todas las sugeridas, no se hace nada.")
        return
    # If Immich date is the same day as the oldest, do nothing
    if immich_date.date() == oldest.date():
        print(f"[DATE CORRECTION] Immich date {immich_date} es del mismo día que la más antigua {oldest}, no se hace nada.")
        return
    # New: If the best candidate is less than 4h different and Immich has time info but candidate is exactly at 00:00:00, keep Immich's date
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