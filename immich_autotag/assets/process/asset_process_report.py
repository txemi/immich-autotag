from typing import List, Optional

import attr

from immich_autotag.assets.albums.analyze_and_assign_album import AlbumAssignmentResult
from immich_autotag.assets.classification_update_result import (
    ClassificationUpdateResult,
)
from immich_autotag.assets.date_correction.core_logic import DateCorrectionStepResult
from immich_autotag.assets.duplicate_tag_logic.analyze_duplicate_classification_tags import (
    DuplicateTagAnalysisResult,
)
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
class AssetProcessReport:
    """
    Collects the results of each step in process_single_asset for a single asset.
    Can generate a summary report and answer if any changes were made.
    Holds explicit attributes for each processing phase.
    """

    tag_conversion_result: Optional[ModificationEntriesList] = None
    date_correction_result: Optional[DateCorrectionStepResult] = None
    duplicate_tag_analysis_result: Optional[DuplicateTagAnalysisResult] = None
    album_assignment_result: Optional[AlbumAssignmentResult] = None
    validate_result: Optional[ClassificationUpdateResult] = None
    # Optionally, keep the old steps list for extensibility/debug
    steps: List[AssetProcessStepResult] = attr.ib(factory=list)

    def any_changes(self) -> bool:
        # Define what counts as a change: if any phase result indicates a change
        # This logic can be refined as needed
        for obj in [
            self.tag_conversion_result,
            self.date_correction_result,
            self.duplicate_tag_analysis_result,
            self.album_assignment_result,
            self.validate_result,
        ]:
            try:
                if obj.changed:  # type: ignore[attr-defined,union-attr]
                    return True
            except (AttributeError, TypeError):
                pass
            if isinstance(obj, list) and obj:
                return True
            if obj is not None and not isinstance(obj, list):
                return True
        return False

    def summary(self) -> str:
        lines = [
            f"Asset process summary: {'CHANGES' if self.any_changes() else 'NO CHANGES'}"
        ]
        if self.tag_conversion_result is not None:
            lines.append(f"Tag conversions: {self.tag_conversion_result}")
        if self.date_correction_result is not None:
            lines.append(f"Date correction: {self.date_correction_result}")
        if self.duplicate_tag_analysis_result is not None:
            lines.append(
                f"Duplicate tag analysis: {self.duplicate_tag_analysis_result}"
            )
        if self.album_assignment_result is not None:
            lines.append(f"Album assignment: {self.album_assignment_result}")
        if self.validate_result is not None:
            lines.append(f"Validation: {self.validate_result}")
        return "\n".join(lines)

    def __str__(self):
        return self.summary()
