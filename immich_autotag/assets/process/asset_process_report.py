from typing import TYPE_CHECKING, List, Optional

import attr

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.assets.classification_validation_result import (
        ClassificationValidationResult,
    )

from immich_autotag.assets.albums.analyze_and_assign_album import AlbumAssignmentReport
from immich_autotag.assets.consistency_checks._album_date_consistency import (
    AlbumDateConsistencyResult,
)
from immich_autotag.assets.date_correction.core_logic import (
    AssetDateCorrector,
    DateCorrectionStepResult,
)
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    DuplicateTagAnalysisReport,
)
from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult
from immich_autotag.report.modification_entries_list import ModificationEntriesList


@attr.s(auto_attribs=True, slots=True)
class AssetProcessStepResult:
    step_name: str
    changed: bool = False
    details: Optional[str] = None
    data: Optional[object] = None

    def __str__(self):
        return f"{self.step_name}: {'CHANGED' if self.changed else 'NO CHANGE'}" + (
            f" | {self.details}" if self.details else ""
        )


@attr.s(auto_attribs=True, slots=True)
class AssetProcessReport(ProcessStepResult):
    """
    Collects the results of each step in process_single_asset for a single asset.
    Can generate a summary report and answer if any changes were made.
    Holds explicit attributes for each processing phase.

    Implements ProcessStepResult protocol with has_changes(), has_errors(), and format() methods.

    Four of the result types implement the ProcessStepResult protocol:
    - ModificationEntriesList (tag_conversion_result)
    - AssetDateCorrector (date_correction_result)
    - AlbumAssignmentReport (album_assignment_result)
    - ClassificationValidationResult (validate_result)

    Other result types (DuplicateTagAnalysisResult) are enum-based and are included in
    reports for completeness but without the protocol interface.
    """

    asset_wrapper: "AssetResponseWrapper"
    tag_conversion_result: Optional[ModificationEntriesList] = None
    date_correction_result: Optional[AssetDateCorrector] = None
    duplicate_tag_analysis_result: Optional[DuplicateTagAnalysisReport] = None
    album_date_consistency_result: Optional[AlbumDateConsistencyResult] = None
    album_assignment_result: Optional[AlbumAssignmentReport] = None
    validate_result: Optional["ClassificationValidationResult"] = None
    # Optionally, keep the old steps list for extensibility/debug
    steps: List[AssetProcessStepResult] = attr.ib(factory=lambda: [])

    def has_changes(self) -> bool:
        """Returns True if any processing step resulted in changes."""
        if self.tag_conversion_result is not None and (
            self.tag_conversion_result.has_changes()
            or self.tag_conversion_result.has_errors()
        ):
            return True

        if (
            self.date_correction_result is not None
            and self.date_correction_result.get_step_result()
            == DateCorrectionStepResult.FIXED
        ):
            return True

        if (
            self.duplicate_tag_analysis_result is not None
            and self.duplicate_tag_analysis_result.has_changes()
        ):
            return True

        if (
            self.album_date_consistency_result is not None
            and self.album_date_consistency_result.has_changes()
        ):
            return True

        if (
            self.album_assignment_result is not None
            and self.album_assignment_result.has_changes()
        ):
            return True

        if self.validate_result is not None:
            return True

        return False

    def has_errors(self) -> bool:
        """Returns True if any processing step encountered errors."""
        if self.tag_conversion_result is not None:
            return self.tag_conversion_result.has_errors()
        return False

    def _get_changes_details(self) -> str:
        """
        Generate a concise string describing what changes were made.

        Treats all result objects uniformly through the ProcessStepResult protocol,
        calling format() on each to obtain symmetric string representation.
        """
        changes: list[str] = []

        # Process results that implement ProcessStepResult protocol
        # These have has_changes(), has_errors(), and format() methods
        if self.tag_conversion_result is not None:
            changes.append(self.tag_conversion_result.format())

        if self.date_correction_result is not None:
            changes.append(self.date_correction_result.format())

        # Enum results (DuplicateTagAnalysisResult)
        # are included directly in summary but not with format() method
        if self.duplicate_tag_analysis_result is not None:
            changes.append(self.duplicate_tag_analysis_result.format())

        if self.album_date_consistency_result is not None:
            changes.append(self.album_date_consistency_result.format())

        if self.album_assignment_result is not None:
            changes.append(self.album_assignment_result.format())

        if self.validate_result is not None:
            changes.append(self.validate_result.format())

        if changes:
            return " | ".join(changes)
        return ""

    def format(self) -> str:
        """Return a formatted string representation of the report."""
        changes_indicator = "✓ CHANGES" if self.has_changes() else "○ NO CHANGES"
        changes_details = self._get_changes_details()
        result = f"[ASSET REPORT] {changes_indicator}"
        if changes_details:
            result += f" | {changes_details}"
        return result

    def any_changes(self) -> bool:
        """Backward-compatible alias for has_changes()."""
        return self.has_changes()

    def summary(self) -> str:
        lines: List[str] = []
        asset_url = self.asset_wrapper.get_immich_photo_url().geturl()

        # Build a single detailed summary line
        changes_indicator = "✓ CHANGES" if self.has_changes() else "○ NO CHANGES"
        changes_details = self._get_changes_details()

        lines.append(f"[ASSET REPORT] {changes_indicator}")
        lines.append(f"  Asset: {asset_url}")

        if changes_details:
            lines.append(f"  Details: {changes_details}")

        # Add individual results for detailed info
        if self.tag_conversion_result is not None:
            lines.append(f"  Tag conversions: {self.tag_conversion_result.format()}")
        if self.date_correction_result is not None:
            lines.append(f"  Date correction: {self.date_correction_result.format()}")
        if self.duplicate_tag_analysis_result is not None:
            lines.append(
                f"  Duplicate tag analysis: {self.duplicate_tag_analysis_result.format()}"
            )
        if self.album_date_consistency_result is not None:
            lines.append(
                "  Album date consistency: "
                f"{self.album_date_consistency_result.format()}"
            )
        if self.album_assignment_result is not None:
            lines.append(f"  Album assignment: {self.album_assignment_result.format()}")
        if self.validate_result is not None:
            lines.append(f"  Validation: {self.validate_result.format()}")

        return "\n".join(lines)

    def __str__(self):
        return self.summary()
