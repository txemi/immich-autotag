from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.utils.date_compare import is_datetime_more_than_days_after

from .asset_date_candidates import AssetDateCandidates
from .asset_date_sources_list import AssetDateSourcesList


@typechecked
def _is_precise_and_rounded_midnight_close(
    dt_precise: datetime, dt_midnight: datetime, threshold_seconds: int = 4 * 3600
) -> bool:
    """
    Devuelve True si dt_precise tiene hora distinta de 00:00:00, dt_midnight es exactamente a medianoche,
    y la diferencia absoluta entre ambos es menor que threshold_seconds.
    """
    diff = abs(
        (
            dt_midnight.astimezone(ZoneInfo("UTC"))
            - dt_precise.astimezone(ZoneInfo("UTC"))
        ).total_seconds()
    )
    return (
        diff < threshold_seconds
        and (dt_precise.hour != 0 or dt_precise.minute != 0 or dt_precise.second != 0)
        and dt_midnight.hour == 0
        and dt_midnight.minute == 0
        and dt_midnight.second == 0
    )


@typechecked
def correct_asset_date(asset_wrapper: AssetResponseWrapper, log: bool = False) -> None:
    """
    Main entry point for asset date correction logic.
    For WhatsApp assets, finds the oldest date among Immich and filename-extracted dates from all duplicates.
    """
    # Always consider all possible date sources, even if there are no duplicates
    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    date_sources_list = AssetDateSourcesList.from_wrappers(asset_wrapper, wrappers)
    flat_candidates = date_sources_list.to_flat_candidates()
    if not flat_candidates:
        if log:
            print(f"[DATE CORRECTION] No date candidates found for asset {asset_wrapper.asset.id}")
        return
    if log:
        print("[DEBUG] Fechas candidatas y sus tipos/tzinfo:")
        for candidate in flat_candidates:
            aware_date = candidate.get_aware_date()
            print(f"  {candidate.source_kind}: {aware_date!r} (type={type(aware_date)}, tzinfo={getattr(aware_date, 'tzinfo', None)})")
    # Usar el método de la lista para obtener el candidato más antiguo (normalizado)
    oldest_candidate = date_sources_list.oldest_candidate()
    oldest: datetime = oldest_candidate.get_aware_date()
    # Get the Immich date (the one visible and modifiable in the UI)
    immich_date: datetime = asset_wrapper.get_best_date()

    # Si la fecha de Immich es la más antigua o igual a la más antigua sugerida, no se hace nada
    if immich_date <= oldest:
        if log:
            print(
                f"[DATE CORRECTION] Immich date {immich_date} ya es la más antigua o igual a la más antigua sugerida ({oldest}), no se hace nada."
            )
        return
    # If Immich date is the same day as the oldest, do nothing
    if immich_date.date() == oldest.date():
        if log:
            print(
                f"[DATE CORRECTION] Immich date {immich_date} es del mismo día que la más antigua {oldest}, no se hace nada."
            )
        return
    # Si la mejor candidata es redondeada a medianoche y está muy cerca (<4h) de la de Immich, y la de Immich tiene hora precisa, no se hace nada
    if _is_precise_and_rounded_midnight_close(
        immich_date, oldest
    ):
        if log:
            print(
                f"[DATE CORRECTION] Immich date {immich_date} tiene hora precisa y la sugerida {oldest} es redondeada y muy cercana (<4h). No se hace nada."
            )
        return
    # Si la diferencia entre la fecha de Immich y la más antigua es menor de 16 horas, no hacer nada (para evitar falsos positivos)
    diff_seconds_abs = abs((immich_date - oldest).total_seconds())
    if diff_seconds_abs < 16 * 3600:
        if log:
            print(f"[DATE CORRECTION] Diferencia entre Immich date y oldest es menor de 16h: {diff_seconds_abs/3600:.2f} horas. No se hace nada.")
        return
    # Nueva lógica: si la fecha de Immich es posterior a la fecha obtenida del nombre del fichero en más de 24h, actualizar
    whatsapp_filename_date = date_sources_list.get_whatsapp_filename_date()
    if whatsapp_filename_date is not None and is_datetime_more_than_days_after(
        immich_date, whatsapp_filename_date, days=1
    ):
        print(
            f"[DATE CORRECTION] Actualizando fecha de Immich a la del nombre del fichero: {whatsapp_filename_date}"
        )
        asset_wrapper.update_date(whatsapp_filename_date)
        print(
            f"[DATE CORRECTION] Fecha de Immich actualizada correctamente a {whatsapp_filename_date}"
        )
        return

    filename_candidates = date_sources_list.filename_candidates()
    if filename_candidates:
        filename_candidate = min(filename_candidates, key=lambda c: c.get_aware_date())
        if is_datetime_more_than_days_after(
            immich_date, filename_candidate.get_aware_date(), days=2
        ):
            print(
                f"[DATE CORRECTION] Actualizando fecha de Immich a la del nombre del fichero (no WhatsApp): {filename_candidate.get_aware_date()} (label: {filename_candidate.source_kind})"
            )
            asset_wrapper.update_date(filename_candidate.get_aware_date())
            print(
                f"[DATE CORRECTION] Fecha de Immich actualizada correctamente a {filename_candidate.get_aware_date()}"
            )
            return
    # Si no se cumple la condición, lanzar excepción como antes
    photo_url_obj = asset_wrapper.get_immich_photo_url()
    photo_url = photo_url_obj.geturl()
    print(f"[DATE CORRECTION][LINK] Asset {asset_wrapper.asset.id} -> {photo_url}")

    # Print both dates in UTC for clarity
    def to_utc(dt: datetime) -> datetime:
        return dt.astimezone(ZoneInfo("UTC")) if dt.tzinfo else dt
    # Print the difference between Immich date and the oldest candidate for debugging
    diff_seconds = (immich_date - oldest).total_seconds()
    diff_timedelta = immich_date - oldest

    immich_utc = to_utc(immich_date)
    oldest_utc = to_utc(oldest)
    msg = (
        f"[DATE CORRECTION] Caso no implementado: Immich date {immich_date} y oldest {oldest} (asset {asset_wrapper.asset.id})\n"
        f"[DATE CORRECTION][UTC] Immich date UTC: {immich_utc}, oldest UTC: {oldest_utc}"
        f"[DATE CORRECTION][DIFF] Immich date - oldest: {diff_timedelta} ({diff_seconds:.1f} seconds)"
    )
    print(msg)
    correct_asset_date(asset_wrapper, log=True)  # Evitar bucle infinito en logs
    raise NotImplementedError(msg)
