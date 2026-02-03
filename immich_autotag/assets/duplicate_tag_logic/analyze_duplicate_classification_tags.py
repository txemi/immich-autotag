from enum import Enum, auto

import attrs
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult
from immich_autotag.types.uuid_wrappers import AssetUUID

from .__compare_classification_tags import compare_classification_tags
from .__get_duplicate_wrappers import get_duplicate_wrappers
from .__mark_and_log_conflict import mark_and_log_conflict
from .__try_autofix import try_autofix
from ._classification_tag_comparison_result import ClassificationTagComparisonResult


class DuplicateTagAnalysisResult(Enum):
    NO_DUPLICATES = auto()
    ALL_EQUAL = auto()
    AUTOFIXED = auto()
    CONFLICT = auto()
    ERROR = auto()


@attrs.define(auto_attribs=True, slots=True, frozen=False)
class DuplicateTagAnalysisReport(ProcessStepResult):
    """
    Analyzes classification consistency across duplicate assets.
    
    This class checks whether all duplicates of a given asset have consistent classification tags.
    When duplicates exist, they should all belong to the same category (classification).
    
    The analysis performs the following checks:
    - Verifies that all duplicate assets have the same classification tags
    - Attempts automatic fix (autofix) when inconsistencies can be resolved automatically
    - Marks conflicts when duplicates have incompatible classifications
    - Tracks statistics about duplicate count, comparisons, autofixes, and errors
    
    The consistency check is critical because duplicate assets represent the same physical content
    and should therefore have the same classification. Inconsistencies may arise from:
    - Manual tagging errors
    - Timing issues during parallel processing
    - Classification rule changes over time
    
    Note: This analysis focuses on classification consistency, not on date consistency
    (which is handled separately by AlbumDateConsistencyResult).
    """
    
    _asset_wrapper: AssetResponseWrapper = attrs.field(repr=False)
    _result: DuplicateTagAnalysisResult = attrs.field(
        init=False, default=None, repr=True
    )
    _autofix_count: int = attrs.field(init=False, default=0, repr=True)
    _conflict_found: bool = attrs.field(init=False, default=False, repr=True)
    _duplicate_count: int = attrs.field(init=False, default=0, repr=True)
    _compared_count: int = attrs.field(init=False, default=0, repr=True)
    _error_count: int = attrs.field(init=False, default=0, repr=True)

    def has_changes(self) -> bool:
        return self._result in (DuplicateTagAnalysisResult.AUTOFIXED,)

    def has_errors(self) -> bool:
        return self._error_count > 0 or self._result == DuplicateTagAnalysisResult.ERROR

    def get_title(self) -> str:
        return "Duplicate classification consistency"

    def get_result(self) -> DuplicateTagAnalysisResult:
        return self._result

    def format(self) -> str:
        parts: list[str] = []
        parts.append(f"duplicates={self._duplicate_count}")
        parts.append(f"compared={self._compared_count}")
        if self._autofix_count:
            parts.append(f"autofix={self._autofix_count}")
        if self._conflict_found:
            parts.append("conflict=1")
        if self._error_count:
            parts.append(f"errors={self._error_count}")
        return f"{self._result.name} ({', '.join(parts)})"

    @classmethod
    def analyze(
        cls, asset_wrapper: AssetResponseWrapper
    ) -> "DuplicateTagAnalysisReport":
        """Create instance and perform analysis"""
        report = cls(asset_wrapper=asset_wrapper)
        report._perform_analysis()
        return report

    def _get_duplicate_ids(
        self, duplicate_wrappers: list[AssetResponseWrapper], asset_id: AssetUUID
    ) -> list[AssetUUID]:
        """Extract duplicate IDs excluding the current asset"""
        return [
            wrapper.get_id()
            for wrapper in duplicate_wrappers
            if wrapper.get_id() != asset_id
        ]

    def _compare_with_duplicate(self, duplicate_wrapper: AssetResponseWrapper):
        """Compare classification tags with a duplicate asset"""
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            f"[DUPLICATE TAGS][INFO] Duplicate asset info:\n{duplicate_wrapper.format_info()}",
            level=LogLevel.FOCUS,
        )
        return compare_classification_tags(self._asset_wrapper, duplicate_wrapper)

    def _try_handle_autofix(
        self,
        duplicate_wrapper: AssetResponseWrapper,
        comp_result,
        error_messages: list[str],
    ) -> bool:
        """Try to handle autofix cases. Returns True if handled, False otherwise"""
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if comp_result.result not in (
            ClassificationTagComparisonResult.AUTOFIX_OTHER,
            ClassificationTagComparisonResult.AUTOFIX_SELF,
        ):
            return False

        if comp_result.tag_info is not None:
            try_autofix(
                self._asset_wrapper,
                duplicate_wrapper,
                comp_result.result,
                comp_result.tag_info,
            )
            self._autofix_count += 1
            return True
        else:
            error_message = (
                "[DUPLICATE TAGS][ERROR] tag_info is None for autofix result "
                f"on asset {self._asset_wrapper.get_id()}"
            )
            log(error_message, level=LogLevel.ERROR)
            error_messages.append(error_message)
            return True

    def _finalize_conflict(
        self, compared_asset_ids: list[AssetUUID], error_messages: list[str]
    ) -> None:
        """Finalize result when a conflict is found"""
        mark_and_log_conflict(self._asset_wrapper)
        self._conflict_found = True
        self._result = DuplicateTagAnalysisResult.CONFLICT
        self._compared_count = len(compared_asset_ids)
        self._error_count = len(error_messages)

    def _finalize_result(
        self,
        duplicate_asset_ids: list[AssetUUID],
        compared_asset_ids: list[AssetUUID],
        error_messages: list[str],
        any_autofix: bool,
        all_equal: bool,
    ) -> None:
        """Determine final result based on analysis"""
        self._compared_count = len(compared_asset_ids)
        self._error_count = len(error_messages)

        if any_autofix:
            self._result = DuplicateTagAnalysisResult.AUTOFIXED
        elif all_equal:
            self._result = DuplicateTagAnalysisResult.ALL_EQUAL
        else:
            self._result = DuplicateTagAnalysisResult.ERROR

    def _perform_analysis(self) -> None:
        """Perform the duplicate tag analysis - main entry point"""
        asset_id = self._asset_wrapper.get_id()
        self._asset_wrapper.get_duplicate_id_as_uuid()

        duplicate_wrappers = get_duplicate_wrappers(self._asset_wrapper)
        duplicate_asset_ids = self._get_duplicate_ids(duplicate_wrappers, asset_id)
        self._duplicate_count = len(duplicate_asset_ids)

        if not duplicate_asset_ids:
            self._result = DuplicateTagAnalysisResult.NO_DUPLICATES
            return

        # Process all duplicates and collect results
        compared_asset_ids: list[AssetUUID] = []
        any_autofix = False
        all_equal = True
        error_messages: list[str] = []

        for duplicate_wrapper in duplicate_wrappers:
            if duplicate_wrapper.get_id() == asset_id:
                continue

            compared_asset_ids.append(duplicate_wrapper.get_id())
            comp_result = self._compare_with_duplicate(duplicate_wrapper)

            if comp_result.result == ClassificationTagComparisonResult.EQUAL:
                continue

            all_equal = False

            # Handle autofix cases
            if self._try_handle_autofix(duplicate_wrapper, comp_result, error_messages):
                any_autofix = True
                continue

            # Handle conflict case (early exit)
            if comp_result.result == ClassificationTagComparisonResult.CONFLICT:
                self._finalize_conflict(compared_asset_ids, error_messages)
                return

        # Finalize based on collected results
        self._finalize_result(
            duplicate_asset_ids,
            compared_asset_ids,
            error_messages,
            any_autofix,
            all_equal,
        )

    def __str__(self) -> str:
        return self.format()


@typechecked
def analyze_duplicate_classification_tags(
    asset_wrapper: AssetResponseWrapper,
) -> DuplicateTagAnalysisReport:
    """
    Checks the classification tags of all duplicates of the given asset.
    - If tags are equal, does nothing.
    - If tags can be autofixed, attempts autofix.
    - If there is a conflict, marks and logs the conflict.
    - Does not raise exceptions; only logs and marks conflicts.
    """
    return DuplicateTagAnalysisReport.analyze(asset_wrapper)
