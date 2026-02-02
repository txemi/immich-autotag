from datetime import datetime
from zoneinfo import ZoneInfo

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.utils.date_compare import is_datetime_more_than_days_after

from ..asset_date_sources_list import AssetDateSourcesList
from .step_result import DateCorrectionStepResult


@typechecked
def is_precise_and_rounded_midnight_close(
    dt_precise: datetime, dt_midnight: datetime, threshold_seconds: int = 4 * 3600
) -> bool:
    """
    Returns True if dt_precise has a time different from 00:00:00, dt_midnight is exactly at midnight,
    and the absolute difference between them is less than threshold_seconds.
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
def check_filename_candidate_and_fix(
    asset_wrapper: AssetResponseWrapper,
    date_sources_list: AssetDateSourcesList,
    immich_date: datetime,
) -> DateCorrectionStepResult:
    """
    Checks if the filename candidate suggests a date correction. If so, updates the date and returns FIXED.
    If no correction is needed, returns CONTINUE. If a condition is met to exit early, returns EXIT.
    """
    # Unificamos: FILENAME, WHATSAPP_FILENAME, IMMICH
    kinds = [
        DateSourceKind.FILENAME,
        DateSourceKind.WHATSAPP_FILENAME,
        DateSourceKind.IMMICH,
    ]
    candidates = date_sources_list.candidates_by_kinds(kinds)
    if not candidates:
        return DateCorrectionStepResult.CONTINUE
    best_candidate = min(candidates, key=lambda c: c.get_aware_date())

    # Use 1.1 days as threshold
    candidate_date = best_candidate.get_aware_date()
    candidate_has_time = (
        candidate_date.hour != 0
        or candidate_date.minute != 0
        or candidate_date.second != 0
    )
    # Case 1: large day difference (as before)
    if is_datetime_more_than_days_after(immich_date, candidate_date, days=1.1):
        log("[DATE CORRECTION][COMPLETE DIAGNOSIS]", level=LogLevel.FOCUS)
        log(date_sources_list.format_full_info(), level=LogLevel.FOCUS)
        log("[DATE CORRECTION][SELECTED CANDIDATE]", level=LogLevel.FOCUS)
        log(best_candidate.format_info(), level=LogLevel.FOCUS)
        log(
            f"[DATE CORRECTION] Updating Immich date to the one from candidate: {candidate_date} (label: {best_candidate.get_source_kind()})",
            level=LogLevel.FOCUS,
        )
        asset_wrapper.update_date(new_date=candidate_date)
        log(
            f"[DATE CORRECTION] Immich date successfully updated to {candidate_date}",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.FIXED
    # Case 2: same date, Immich at midnight, candidate has real time and is older
    if candidate_has_time and candidate_date < immich_date:
        log("[DATE CORRECTION][TIME PRECISION]", level=LogLevel.FOCUS)
        log(date_sources_list.format_full_info(), level=LogLevel.FOCUS)
        log("[DATE CORRECTION][SELECTED CANDIDATE]", level=LogLevel.FOCUS)
        log(best_candidate.format_info(), level=LogLevel.FOCUS)
        log(
            f"[DATE CORRECTION] Updating Immich time to the one from candidate: {candidate_date} (label: {best_candidate.get_source_kind()})",
            level=LogLevel.FOCUS,
        )
        asset_wrapper.update_date(new_date=candidate_date)
        log(
            f"[DATE CORRECTION] Immich date successfully updated to {candidate_date}",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.FIXED
    return DateCorrectionStepResult.CONTINUE
