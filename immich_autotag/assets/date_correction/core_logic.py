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
    # Unificamos: FILENAME, WHATSAPP_FILENAME, IMMICH
    kinds = [DateSourceKind.FILENAME, DateSourceKind.WHATSAPP_FILENAME, DateSourceKind.IMMICH]
    candidates = date_sources_list.candidates_by_kinds(kinds)
    if not candidates:
        return DateCorrectionStepResult.CONTINUE
    best_candidate = min(candidates, key=lambda c: c.get_aware_date())
    from immich_autotag.utils.date_compare import is_datetime_more_than_days_after

    # Usar 1.1 días como umbral
    if is_datetime_more_than_days_after(
        immich_date, best_candidate.get_aware_date(), days=1.1
    ):
        print(
            f"[DATE CORRECTION] Updating Immich date to the one from candidate: {best_candidate.get_aware_date()} (label: {best_candidate.source_kind})"
        )
        # todo: utiliza date_sources_list.format_full_info() para el diagnóstico completo y tambien logea best_candidate con la funcion format_info()
        asset_wrapper.update_date(best_candidate.get_aware_date())
        print(
            f"[DATE CORRECTION] Immich date successfully updated to {best_candidate.get_aware_date()}"
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
    # Always consider all possible date sources, even if there are no duplicates
    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    date_sources_list = AssetDateSourcesList.from_wrappers(asset_wrapper, wrappers)
    flat_candidates = date_sources_list.to_flat_candidates()
    if not flat_candidates:
        if log:
            print(
                f"[DATE CORRECTION] No date candidates found for asset {asset_wrapper.asset.id}"
            )
        return
    if log:
        print("[DEBUG] Candidate dates and their types/tzinfo:")
        for candidate in flat_candidates:
            aware_date = candidate.get_aware_date()
            print(
                f"  {candidate.source_kind}: {aware_date!r} (type={type(aware_date)}, tzinfo={getattr(aware_date, 'tzinfo', None)})"
            )
    # Use the list method to get the oldest candidate (normalized)
    oldest_candidate = date_sources_list.oldest_candidate()
    oldest: datetime = oldest_candidate.get_aware_date()
    # Get the Immich date (the one visible and modifiable in the UI)
    immich_date: datetime = asset_wrapper.get_best_date()

    # If the Immich date is the oldest or equal to the oldest suggested, do nothing
    if immich_date <= oldest:
        if log:
            print(
                f"[DATE CORRECTION] Immich date {immich_date} is already the oldest or equal to the oldest suggested ({oldest}), nothing to do."
            )
        return
    # If Immich date is the same day as the oldest, do nothing
    if immich_date.date() == oldest.date():
        if log:
            print(
                f"[DATE CORRECTION] Immich date {immich_date} is the same day as the oldest {oldest}, nothing to do."
            )
        return
    # If the best candidate is rounded to midnight and is very close (<4h) to the Immich date, and the Immich date is precise, do nothing
    if _is_precise_and_rounded_midnight_close(immich_date, oldest):
        if log:
            print(
                f"[DATE CORRECTION] Immich date {immich_date} is precise and the suggested {oldest} is rounded and very close (<4h). Nothing to do."
            )
        return
    # If the difference between Immich date and the oldest is less than a threshold of hours, do nothing (to avoid false positives). This threshold will be reduced as we test and fix more cases.
    diff_seconds_abs = abs((immich_date - oldest).total_seconds())
    if diff_seconds_abs < 20 * 3600:
        if log:
            print(
                f"[DATE CORRECTION] Difference between Immich date and oldest is less than 16h: {diff_seconds_abs/3600:.2f} hours. Nothing to do."
            )
        return
    # Ya no es necesario el caso WhatsApp: la lógica unificada lo cubre

    # Check if filename-based correction should be applied
    step_result = _check_filename_candidate_and_fix(
        asset_wrapper, date_sources_list, immich_date
    )
    if DateCorrectionStepResult.should_exit(step_result):
        return
    # else, continue processing

    # If none of the above conditions are met, raise an error as before
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
        f"[DATE CORRECTION] Unhandled case: Immich date {immich_date} and oldest {oldest} (asset {asset_wrapper.asset.id})\n"
        f"[DATE CORRECTION][UTC] Immich date UTC: {immich_utc}, oldest UTC: {oldest_utc}"
        f"[DATE CORRECTION][DIFF] Immich date - oldest: {diff_timedelta} ({diff_seconds:.1f} seconds)\n"
        f"\n[DIAGNÓSTICO COMPLETO]\n{date_sources_list.format_full_info()}"
    )
    print(msg)
    raise NotImplementedError(msg)
