from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from immich_autotag.classification.match_result_list import MatchResultList
    from immich_autotag.report.modification_entries_list import ModificationEntriesList

from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ClassificationValidationResult(ProcessStepResult):
    """
    Encapsulates the complete result of classification validation.

    Contains both the cause (which rules matched) and consequence (what modifications were applied).
    This allows upper layers to understand what happened during classification validation.

    Attributes (private):
        _match_results: The MatchResultList containing all matched classification rules (the cause)
        _modifications: The ModificationEntriesList with all tag additions/removals (the consequence)
    """

    _match_results: "MatchResultList" = attrs.field(
        alias="match_results", repr=lambda matches: f"matches={len(matches)}"
    )
    _modifications: "ModificationEntriesList" = attrs.field(
        alias="modifications", repr=lambda mods: f"modifications={len(mods)}"
    )

    def match_results(self) -> "MatchResultList":
        """Get the match results (which rules matched)."""
        return self._match_results

    def modifications(self) -> "ModificationEntriesList":
        """Get the modifications (what tags were added/removed)."""
        return self._modifications

    def has_changes(self) -> bool:
        """Returns True if any modifications were applied during validation."""
        return len(self._modifications) > 0

    def has_errors(self) -> bool:
        """Returns True if validation resulted in errors or warnings."""
        return self._modifications.has_errors()

    def get_title(self) -> str:
        return "Classification validation"

    def get_events(self) -> "ModificationEntriesList":
        """Returns all modification events from the classification validation."""
        return self._modifications

    def format(self) -> str:
        """
        Format the classification validation result with status information.

        Shows the classification status (CLASSIFIED, CONFLICT, or UNCLASSIFIED)
        and the number of matches and modifications.

        Returns:
            A formatted string describing the classification state.
        """
        from immich_autotag.classification.classification_status import (
            ClassificationStatus,
        )

        status = self._match_results.classification_status()
        match_count = len(self._match_results)
        modification_count = len(self._modifications)

        status_display = {
            ClassificationStatus.CLASSIFIED: f"✓ CLASSIFIED ({match_count} rule{'s' if match_count != 1 else ''})",
            ClassificationStatus.CONFLICT: f"⚠ CONFLICT ({match_count} conflicting rules)",
            ClassificationStatus.UNCLASSIFIED: "✗ UNCLASSIFIED (no matches)",
        }

        status_str = status_display.get(status, "? UNKNOWN")

        if modification_count > 0:
            modifications_str = f", {modification_count} modification{'s' if modification_count != 1 else ''} applied"
        else:
            modifications_str = ", no modifications"

        return f"{status_str}{modifications_str}"
