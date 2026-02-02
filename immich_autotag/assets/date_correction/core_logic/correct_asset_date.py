from datetime import datetime
from zoneinfo import ZoneInfo

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log

from ..asset_date_sources_list import AssetDateSourcesList
from ._helpers import check_filename_candidate_and_fix, is_precise_and_rounded_midnight_close
from .step_result import DateCorrectionStepResult


@typechecked
def correct_asset_date(
    asset_wrapper: AssetResponseWrapper, log_flag: bool = False
) -> DateCorrectionStepResult:
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

    wrappers = asset_wrapper.get_all_duplicate_wrappers(include_self=True)
    date_sources_list = AssetDateSourcesList.from_wrappers(asset_wrapper, wrappers)
    flat_candidates = date_sources_list.to_flat_candidates()
    immich_date: datetime = asset_wrapper.get_best_date()

    step_result = check_filename_candidate_and_fix(
        asset_wrapper, date_sources_list, immich_date
    )
    if DateCorrectionStepResult.should_exit(step_result):
        log(
            f"[DATE CORRECTION] Date corrected by filename for asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return step_result

    if not flat_candidates:
        log(
            f"[DATE CORRECTION] No date candidates found for asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.EXIT

    oldest_candidate = date_sources_list.oldest_candidate()
    if oldest_candidate is None:
        log(
            f"[DATE CORRECTION] No valid oldest candidate found for asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.EXIT
    oldest: datetime = oldest_candidate.get_aware_date()

    if immich_date <= oldest:
        log(
            f"[DATE CORRECTION] Immich date {immich_date} is already the oldest or equal to the oldest suggested ({oldest}), nothing to do. Asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.EXIT
    if immich_date.date() == oldest.date():
        log(
            f"[DATE CORRECTION] Immich date {immich_date} is the same day as the oldest {oldest}, nothing to do. Asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.EXIT
    if is_precise_and_rounded_midnight_close(immich_date, oldest):
        log(
            f"[DATE CORRECTION] Immich date {immich_date} is precise and the suggested {oldest} is rounded and very close (<4h). Nothing to do. Asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.EXIT
    diff_seconds_abs = abs((immich_date - oldest).total_seconds())
    if diff_seconds_abs < 20 * 3600:
        log(
            f"[DATE CORRECTION] Difference between Immich date and oldest is less than 16h: {diff_seconds_abs/3600:.2f} hours. Nothing to do. Asset {asset_wrapper.get_id()} ({asset_wrapper.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return DateCorrectionStepResult.EXIT

    photo_url_obj = asset_wrapper.get_immich_photo_url()
    photo_url = photo_url_obj.geturl()
    log(
        f"[DATE CORRECTION][LINK] Asset {asset_wrapper.get_id()} -> {photo_url}",
        level=LogLevel.FOCUS,
    )

    def to_utc(dt: datetime) -> datetime:
        return dt.astimezone(ZoneInfo("UTC")) if dt.tzinfo else dt

    diff_seconds = (immich_date - oldest).total_seconds()
    diff_timedelta = immich_date - oldest

    immich_utc = to_utc(immich_date)
    oldest_utc = to_utc(oldest)
    msg = (
        f"[DATE CORRECTION] Unhandled case: Immich date {immich_date} and oldest {oldest} (asset {asset_wrapper.get_id()})\n"
        f"[DATE CORRECTION][UTC] Immich date UTC: {immich_utc}, oldest UTC: {oldest_utc}"
        f"[DATE CORRECTION][DIFF] Immich date - oldest: {diff_timedelta} ({diff_seconds:.1f} seconds)\n"
        f"\n[COMPLETE DIAGNOSIS]\n{date_sources_list.format_full_info()}"
    )
    log(msg, level=LogLevel.FOCUS)
    raise NotImplementedError(msg)
