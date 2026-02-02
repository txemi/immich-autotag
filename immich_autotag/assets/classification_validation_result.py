from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.classification.match_result_list import MatchResultList
    from immich_autotag.report.modification_entries_list import ModificationEntriesList


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ClassificationValidationResult:
    """
    Encapsulates the complete result of classification validation.
    
    Contains both the cause (which rules matched) and consequence (what modifications were applied).
    This allows upper layers to understand what happened during classification validation.
    
    Attributes (private):
        _match_results: The MatchResultList containing all matched classification rules (the cause)
        _modifications: The ModificationEntriesList with all tag additions/removals (the consequence)
    """

    _match_results: "MatchResultList" = attrs.field(alias="match_results", repr=lambda matches: f"matches={len(matches)}")
    _modifications: "ModificationEntriesList" = attrs.field(alias="modifications", repr=lambda mods: f"modifications={len(mods)}")

    def match_results(self) -> "MatchResultList":
        """Get the match results (which rules matched)."""
        return self._match_results

    def modifications(self) -> "ModificationEntriesList":
        """Get the modifications (what tags were added/removed)."""
        return self._modifications
