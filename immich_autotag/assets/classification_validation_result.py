from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from immich_autotag.classification.match_result_list import MatchResultList
    from immich_autotag.report.modification_entries_list import ModificationEntriesList


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ClassificationValidationResult:
    """
    Encapsulates the complete result of classification validation.

    Contains both the cause (which rules matched) and consequence (what modifications were applied).
    This allows upper layers to understand what happened during classification validation.

    Attributes:
        match_results: The MatchResultList containing all matched classification rules (the cause)
        modifications: The ModificationEntriesList with all tag additions/removals (the consequence)
        rule_set: The ClassificationRuleSet used for classification
        asset: The AssetResponseWrapper being classified
        has_tags: Whether the asset has any tags
        has_albums: Whether the asset belongs to any albums
    """

    match_results: "MatchResultList"
    modifications: "ModificationEntriesList"
