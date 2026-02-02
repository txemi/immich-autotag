from datetime import datetime
from zoneinfo import ZoneInfo

import attrs
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log

from ..asset_date_sources_list import AssetDateSourcesList
from ._helpers import check_filename_candidate_and_fix, is_precise_and_rounded_midnight_close
from .step_result import DateCorrectionStepResult


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class AssetDateCorrector:
    """
    Handles date correction logic for assets.
    
    This class encapsulates the logic for correcting asset dates based on various sources.
    After executing the correction, you can query the internal state to understand
    what happened during the process.
    """
    
    asset_wrapper: AssetResponseWrapper
    
    # Private state (initialized after execute())
    _date_sources_list: AssetDateSourcesList = attrs.field(default=None, init=False, repr=False)
    _selected_candidate: object = attrs.field(default=None, init=False, repr=False)
    _step_result: DateCorrectionStepResult = attrs.field(default=None, init=False, repr=False)
    _reasoning: str = attrs.field(default=None, init=False, repr=False)
    
    @typechecked
    def execute(self, log_flag: bool = False) -> DateCorrectionStepResult:
        """
        Main entry point for asset date correction logic.

        Policy and structure:
        - This method is intentionally organized as a sequence of early returns for all conditions 
          where no action is needed (fail-fast, exit-early philosophy).
        - For conditions where a correction is clearly required, the update is performed immediately 
          and the method returns.
        - Only if none of the above conditions match (i.e., an unhandled or ambiguous case), 
          an error is raised at the end to ensure no silent failures.
        - This approach prioritizes clarity, explicitness, and robustness over minimalism, 
          making the logic easy to audit and debug.

        For WhatsApp assets, finds the oldest date among Immich and filename-extracted dates 
        from all duplicates. Applies all relevant heuristics and thresholds to avoid false positives.
        
        Returns:
            DateCorrectionStepResult indicating the outcome of the correction attempt.
        """

        wrappers = self.asset_wrapper.get_all_duplicate_wrappers(include_self=True)
        self._date_sources_list = AssetDateSourcesList.from_wrappers(self.asset_wrapper, wrappers)
        flat_candidates = self._date_sources_list.to_flat_candidates()
        immich_date: datetime = self.asset_wrapper.get_best_date()

        step_result = check_filename_candidate_and_fix(
            self.asset_wrapper, self._date_sources_list, immich_date
        )
        if DateCorrectionStepResult.should_exit(step_result):
            self._step_result = step_result
            self._reasoning = "Date corrected by filename"
            log(
                f"[DATE CORRECTION] Date corrected by filename for asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return step_result

        if not flat_candidates:
            self._step_result = DateCorrectionStepResult.EXIT
            self._reasoning = "No date candidates found"
            log(
                f"[DATE CORRECTION] No date candidates found for asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return DateCorrectionStepResult.EXIT

        oldest_candidate = self._date_sources_list.oldest_candidate()
        if oldest_candidate is None:
            self._step_result = DateCorrectionStepResult.EXIT
            self._reasoning = "No valid oldest candidate found"
            log(
                f"[DATE CORRECTION] No valid oldest candidate found for asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return DateCorrectionStepResult.EXIT
        
        self._selected_candidate = oldest_candidate
        oldest: datetime = oldest_candidate.get_aware_date()

        if immich_date <= oldest:
            self._step_result = DateCorrectionStepResult.EXIT
            self._reasoning = "Immich date is already the oldest or equal"
            log(
                f"[DATE CORRECTION] Immich date {immich_date} is already the oldest or equal to the oldest suggested ({oldest}), nothing to do. Asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return DateCorrectionStepResult.EXIT
        if immich_date.date() == oldest.date():
            self._step_result = DateCorrectionStepResult.EXIT
            self._reasoning = "Immich date is the same day as the oldest"
            log(
                f"[DATE CORRECTION] Immich date {immich_date} is the same day as the oldest {oldest}, nothing to do. Asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return DateCorrectionStepResult.EXIT
        if is_precise_and_rounded_midnight_close(immich_date, oldest):
            self._step_result = DateCorrectionStepResult.EXIT
            self._reasoning = "Immich date is precise and suggested is rounded and very close (<4h)"
            log(
                f"[DATE CORRECTION] Immich date {immich_date} is precise and the suggested {oldest} is rounded and very close (<4h). Nothing to do. Asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return DateCorrectionStepResult.EXIT
        diff_seconds_abs = abs((immich_date - oldest).total_seconds())
        if diff_seconds_abs < 20 * 3600:
            self._step_result = DateCorrectionStepResult.EXIT
            self._reasoning = "Difference between Immich date and oldest is less than 20h"
            log(
                f"[DATE CORRECTION] Difference between Immich date and oldest is less than 16h: {diff_seconds_abs/3600:.2f} hours. Nothing to do. Asset {self.asset_wrapper.get_id()} ({self.asset_wrapper.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
            return DateCorrectionStepResult.EXIT

        photo_url_obj = self.asset_wrapper.get_immich_photo_url()
        photo_url = photo_url_obj.geturl()
        log(
            f"[DATE CORRECTION][LINK] Asset {self.asset_wrapper.get_id()} -> {photo_url}",
            level=LogLevel.FOCUS,
        )

        def to_utc(dt: datetime) -> datetime:
            return dt.astimezone(ZoneInfo("UTC")) if dt.tzinfo else dt

        diff_seconds = (immich_date - oldest).total_seconds()
        diff_timedelta = immich_date - oldest

        immich_utc = to_utc(immich_date)
        oldest_utc = to_utc(oldest)
        msg = (
            f"[DATE CORRECTION] Unhandled case: Immich date {immich_date} and oldest {oldest} (asset {self.asset_wrapper.get_id()})\n"
            f"[DATE CORRECTION][UTC] Immich date UTC: {immich_utc}, oldest UTC: {oldest_utc}"
            f"[DATE CORRECTION][DIFF] Immich date - oldest: {diff_timedelta} ({diff_seconds:.1f} seconds)\n"
            f"\n[COMPLETE DIAGNOSIS]\n{self._date_sources_list.format_full_info()}"
        )
        log(msg, level=LogLevel.FOCUS)
        self._step_result = DateCorrectionStepResult.EXIT
        self._reasoning = "Unhandled case"
        raise NotImplementedError(msg)

    @typechecked
    def get_step_result(self) -> DateCorrectionStepResult:
        """Get the result of the date correction execution."""
        return self._step_result
    
    @typechecked
    def get_selected_candidate(self) -> object:
        """Get the candidate that was selected during the correction process."""
        return self._selected_candidate
    
    @typechecked
    def get_date_sources_list(self) -> AssetDateSourcesList:
        """Get the complete list of date sources that were evaluated."""
        return self._date_sources_list
    
    @typechecked
    def get_reasoning(self) -> str:
        """Get a text description of why the correction resulted in the current state."""
        return self._reasoning
    
    @typechecked
    def format_diagnosis(self) -> str:
        """
        Format a complete diagnosis of what happened during the correction process.
        
        Returns:
            A formatted string with detailed information about the correction attempt.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DATE CORRECTION DIAGNOSIS")
        lines.append("=" * 60)
        lines.append(f"Asset ID: {self.asset_wrapper.get_id()}")
        lines.append(f"Asset Name: {self.asset_wrapper.get_original_file_name()}")
        lines.append(f"Result: {self._step_result}")
        lines.append(f"Reasoning: {self._reasoning}")
        
        if self._selected_candidate:
            lines.append("")
            lines.append("Selected Candidate:")
            lines.append(self._selected_candidate.format_info())
        
        if self._date_sources_list:
            lines.append("")
            lines.append("All Date Sources:")
            lines.append(self._date_sources_list.format_full_info())
        
        lines.append("=" * 60)
        return "\n".join(lines)
