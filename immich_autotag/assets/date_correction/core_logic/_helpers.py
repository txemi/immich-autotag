from datetime import datetime
from zoneinfo import ZoneInfo

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import is_log_level_enabled, log
from immich_autotag.utils.date_compare import is_datetime_more_than_days_after

from ..asset_date_candidate import AssetDateCandidate
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
def to_extraction_timezone(dt: datetime) -> datetime:
    """
    Returns dt expressed in the configured extraction timezone (same instant, local wall time).

    Immich takes the display timezone of an asset from the offset of the date we send. A date sent
    as UTC (+00:00) shows its UTC wall time: a screenshot taken at 11:01 in Madrid (09:01Z),
    copied to a duplicate as 09:01+00:00, was shown there as 09:01. Sending 11:01+02:00 keeps it
    at 11:01. Falls back to dt unchanged if no timezone is configured.
    """
    from immich_autotag.config.manager import ConfigManager

    config = ConfigManager.get_instance().get_config()
    duplicate_processing = config.duplicate_processing
    if duplicate_processing is None or duplicate_processing.date_correction is None:
        return dt
    tz_name = duplicate_processing.date_correction.extraction_timezone
    if not tz_name:
        return dt
    return dt.astimezone(ZoneInfo(tz_name))


@typechecked
def _apply_candidate(
    asset_wrapper: AssetResponseWrapper,
    date_sources_list: AssetDateSourcesList,
    best_candidate: AssetDateCandidate,
    header: str,
    what: str,
) -> DateCorrectionStepResult:
    candidate_date = to_extraction_timezone(best_candidate.get_aware_date())
    log(header, level=LogLevel.FOCUS)
    if is_log_level_enabled(LogLevel.FOCUS):
        log(date_sources_list.format_full_info(), level=LogLevel.FOCUS)
    log("[DATE CORRECTION][SELECTED CANDIDATE]", level=LogLevel.FOCUS)
    log(best_candidate.format_info(), level=LogLevel.FOCUS)
    log(
        f"[DATE CORRECTION] Updating Immich {what} to the one from candidate: {candidate_date} (label: {best_candidate.get_source_kind()})",
        level=LogLevel.FOCUS,
    )
    asset_wrapper.update_date(new_date=candidate_date)
    log(
        f"[DATE CORRECTION] Immich date successfully updated to {candidate_date}",
        level=LogLevel.FOCUS,
    )
    return DateCorrectionStepResult.FIXED


# A date written in the asset's own filename is the moment that asset was taken. Duplicates in Immich
# are visually similar assets, not copies of the same file: three screenshots of the same screen taken
# hours apart are a duplicate group, and each keeps its own time. txemi, Q1678 (25-oct-2026).
OWN_DATE_KINDS = [DateSourceKind.FILENAME, DateSourceKind.WHATSAPP_FILENAME]
GROUP_DATE_KINDS = [
    DateSourceKind.FILENAME,
    DateSourceKind.WHATSAPP_FILENAME,
    DateSourceKind.IMMICH,
]


@typechecked
def check_filename_candidate_and_fix(
    asset_wrapper: AssetResponseWrapper,
    date_sources_list: AssetDateSourcesList,
    immich_date: datetime,
) -> DateCorrectionStepResult:
    """
    Checks if a filename date suggests a date correction. If so, updates the date and returns FIXED.

    Priority:
    1. The asset's own filename date (FILENAME, WHATSAPP_FILENAME). If it has one, the duplicates are
       not consulted, and the result is FIXED or EXIT, never CONTINUE.
    2. Only if the asset has no date of its own: the oldest FILENAME, WHATSAPP_FILENAME or IMMICH date
       of the duplicate group. If no correction is needed, returns CONTINUE.
    """
    own_candidates = date_sources_list.own_candidates_by_kinds(OWN_DATE_KINDS)
    if own_candidates:
        candidates = own_candidates
    else:
        candidates = date_sources_list.candidates_by_kinds(GROUP_DATE_KINDS)
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
        return _apply_candidate(
            asset_wrapper,
            date_sources_list,
            best_candidate,
            "[DATE CORRECTION][COMPLETE DIAGNOSIS]",
            "date",
        )
    # Case 2: same date, Immich at midnight, candidate has real time and is older
    if candidate_has_time and candidate_date < immich_date:
        return _apply_candidate(
            asset_wrapper,
            date_sources_list,
            best_candidate,
            "[DATE CORRECTION][TIME PRECISION]",
            "time",
        )
    if own_candidates:
        return DateCorrectionStepResult.EXIT
    return DateCorrectionStepResult.CONTINUE
