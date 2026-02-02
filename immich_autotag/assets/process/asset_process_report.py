from typing import TYPE_CHECKING, List, Optional

import attr

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.assets.classification_validation_result import (
        ClassificationValidationResult,
    )

from immich_autotag.assets.albums.analyze_and_assign_album import AlbumAssignmentResult
from immich_autotag.assets.date_correction.core_logic import DateCorrectionStepResult
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    DuplicateTagAnalysisResult,
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

    Implements ProcessStepResult protocol with has_changes() and has_errors() methods.
    """

    asset_wrapper: "AssetResponseWrapper"
    tag_conversion_result: Optional[ModificationEntriesList] = None
    date_correction_result: Optional[DateCorrectionStepResult] = None
    duplicate_tag_analysis_result: Optional[DuplicateTagAnalysisResult] = None
    album_assignment_result: Optional[AlbumAssignmentResult] = None
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
            and self.date_correction_result == DateCorrectionStepResult.FIXED
        ):
            return True

        if (
            self.duplicate_tag_analysis_result is not None
            and self.duplicate_tag_analysis_result
            != DuplicateTagAnalysisResult.NO_DUPLICATES
        ):
            return True

        if self.album_assignment_result is not None:
            return True

        if self.validate_result is not None:
            return True

        return False

    def has_errors(self) -> bool:
        """Returns True if any processing step encountered errors."""
        if self.tag_conversion_result is not None:
            return self.tag_conversion_result.has_errors()
        return False

    def any_changes(self) -> bool:
        """Backward-compatible alias for has_changes()."""
        return self.has_changes()

    def _get_changes_details(self) -> str:
        """Generate a concise string describing what changes were made."""
        changes: list[str] = []

        # Check tag conversions
        if self.tag_conversion_result is not None:
            result_str = str(self.tag_conversion_result).lower()
            if (
                "added" in result_str
                or "removed" in result_str
                or "modified" in result_str
            ):
                changes.append("Tags modified")

        # Check date corrections
        if self.date_correction_result is not None:
            result_str = str(self.date_correction_result).lower()
            if (
                "updated" in result_str
                or "corrected" in result_str
                or "fixed" in result_str
            ):
                changes.append("Date corrected")

        # Check album assignment
        if self.album_assignment_result is not None:
            result_str = str(self.album_assignment_result).lower()
            if "assigned" in result_str or "classified" in result_str:
                changes.append("Album assigned")

        # Check validation result for classification status
        if self.validate_result is not None:
            changes.append(self.validate_result.format())

        if changes:
            return " | ".join(changes)
        return ""

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
            lines.append(f"  Tag conversions: {self.tag_conversion_result}")
        if self.date_correction_result is not None:
            lines.append(f"  Date correction: {self.date_correction_result}")
        if self.duplicate_tag_analysis_result is not None:
            lines.append(
                f"  Duplicate tag analysis: {self.duplicate_tag_analysis_result}"
            )
        if self.album_assignment_result is not None:
            lines.append(f"  Album assignment: {self.album_assignment_result}")
        if self.validate_result is not None:
            lines.append(f"  Validation: {self.validate_result.format()}")

        return "\n".join(lines)

    def __str__(self):
        return self.summary()
