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


from enum import Enum, auto


# Enum for control flow in date correction steps
class DateCorrectionStepResult(Enum):

    CONTINUE = auto()  # Continue processing
    EXIT = auto()  # Stop processing, nothing to do
    FIXED = auto()  # Date was fixed, stop processing

    @staticmethod
    def should_exit(result: "DateCorrectionStepResult") -> bool:
        """Return True if the result means processing should exit (FIXED or EXIT)."""
        return result in (DateCorrectionStepResult.FIXED, DateCorrectionStepResult.EXIT)


@typechecked
def _check_filename_candidate_and_fix(
    asset_wrapper: AssetResponseWrapper,
    date_sources_list: AssetDateSourcesList,
    immich_date: datetime,
) -> "DateCorrectionStepResult":
    """
    Checks if the filename candidate suggests a date correction. If so, updates the date and returns FIXED.
    If no correction is needed, returns CONTINUE. If a condition is met to exit early, returns EXIT.
    """
    from immich_autotag.assets.date_correction.date_source_kind import DateSourceKind
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

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
    from immich_autotag.utils.date_compare import is_datetime_more_than_days_after

    # Use 1.1 days as threshold
    candidate_date = best_candidate.get_aware_date()
    immich_time_is_midnight = (
        immich_date.hour == 0 and immich_date.minute == 0 and immich_date.second == 0
    )
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
            f"[DATE CORRECTION] Updating Immich date to the one from candidate: {candidate_date} (label: {best_candidate.source_kind})",
            level=LogLevel.FOCUS,
        )
        asset_wrapper.update_date(candidate_date)
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
            f"[DATE CORRECTION] Updating Immich time to the one from candidate: {candidate_date} (label: {best_candidate.source_kind})",
            level=LogLevel.FOCUS,
        )
        asset_wrapper.update_date(candidate_date)
        log(
            f"[DATE CORRECTION] Immich date successfully updated to {candidate_date}",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.FIXED
    return DateCorrectionStepResult.CONTINUE


@typechecked
def correct_asset_date(asset_wrapper: AssetResponseWrapper, log: bool = False) -> None:
    """
    Main entry point for asset date correction logic.

    Policy and structure:
    - This function is intentionally organized as a sequence of early returns for all conditions where no action is needed (fail-fast, exit-early philosophy).
    - For conditions where a correction is clearly required, the update is performed immediately and the function returns.
    - Only if none of the above conditions match (i.e., an unhandled or ambiguous case), an error is raised at the end to ensure no silent failures.
    - This approach prioritizes clarity, explicitness, and robustness over minimalism, making the logic easy to audit and debug.

    For WhatsApp assets, finds the oldest date among Immich and filename-extracted dates from all duplicates.
    Applies all relevant heuristics and thresholds to avoid false positives.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    date_sources_list = AssetDateSourcesList.from_wrappers(asset_wrapper, wrappers)
    flat_candidates = date_sources_list.to_flat_candidates()
    immich_date: datetime = asset_wrapper.get_best_date()

    step_result = _check_filename_candidate_and_fix(
        asset_wrapper, date_sources_list, immich_date
    )
    if DateCorrectionStepResult.should_exit(step_result):
        log(
            f"[DATE CORRECTION] Date corrected by filename for asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
        return

    if not flat_candidates:
        log(
            f"[DATE CORRECTION] No date candidates found for asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
        return

    oldest_candidate = date_sources_list.oldest_candidate()
    oldest: datetime = oldest_candidate.get_aware_date()

    if immich_date <= oldest:
        log(
            f"[DATE CORRECTION] Immich date {immich_date} is already the oldest or equal to the oldest suggested ({oldest}), nothing to do. Asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
        return
    if immich_date.date() == oldest.date():
        log(
            f"[DATE CORRECTION] Immich date {immich_date} is the same day as the oldest {oldest}, nothing to do. Asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
        return
    if _is_precise_and_rounded_midnight_close(immich_date, oldest):
        log(
            f"[DATE CORRECTION] Immich date {immich_date} is precise and the suggested {oldest} is rounded and very close (<4h). Nothing to do. Asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
        return
    diff_seconds_abs = abs((immich_date - oldest).total_seconds())
    if diff_seconds_abs < 20 * 3600:
        log(
            f"[DATE CORRECTION] Difference between Immich date and oldest is less than 16h: {diff_seconds_abs/3600:.2f} hours. Nothing to do. Asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
        return

    photo_url_obj = asset_wrapper.get_immich_photo_url()
    photo_url = photo_url_obj.geturl()
    log(
        f"[DATE CORRECTION][LINK] Asset {asset_wrapper.asset.id} -> {photo_url}",
        level=LogLevel.FOCUS,
    )

    def to_utc(dt: datetime) -> datetime:
        return dt.astimezone(ZoneInfo("UTC")) if dt.tzinfo else dt

    diff_seconds = (immich_date - oldest).total_seconds()
    diff_timedelta = immich_date - oldest

    immich_utc = to_utc(immich_date)
    oldest_utc = to_utc(oldest)
    msg = (
        f"[DATE CORRECTION] Unhandled case: Immich date {immich_date} and oldest {oldest} (asset {asset_wrapper.asset.id})\n"
        f"[DATE CORRECTION][UTC] Immich date UTC: {immich_utc}, oldest UTC: {oldest_utc}"
        f"[DATE CORRECTION][DIFF] Immich date - oldest: {diff_timedelta} ({diff_seconds:.1f} seconds)\n"
        f"\n[COMPLETE DIAGNOSIS]\n{date_sources_list.format_full_info()}"
    )
    log(msg, level=LogLevel.FOCUS)
    raise NotImplementedError(msg)
