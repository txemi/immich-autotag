"""Private core logic for analyzing and assigning albums."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.classification.classification_rule_set import (
    ClassificationRuleSet,
)
from immich_autotag.classification.classification_status import ClassificationStatus

from ._handle_classification_conflict import _handle_classification_conflict
from ._handle_classified_asset import _handle_classified_asset
from ._handle_duplicate_conflicts import _handle_duplicate_conflicts
from ._handle_unclassified_asset import _handle_unclassified_asset
from .album_assignment_result import AlbumAssignmentResult

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.report.modification_report import ModificationReport


@typechecked
def _analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
) -> AlbumAssignmentResult:
    """
    Handles all logic related to analyzing potential albums for an asset, deciding assignment, and handling conflicts.
    """
    from immich_autotag.assets.albums.album_decision import AlbumDecision

    album_decision = AlbumDecision(asset_wrapper=asset_wrapper)

    # 1. Handle duplicate conflicts
    _handle_duplicate_conflicts(asset_wrapper, album_decision)

    # 2. Check classification status
    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    match_results = rule_set.matching_rules(asset_wrapper)
    status = match_results.classification_status()

    # 3. Handle based on status
    if status == ClassificationStatus.CLASSIFIED:
        return _handle_classified_asset(asset_wrapper, tag_mod_report)

    if status == ClassificationStatus.CONFLICT:
        return _handle_classification_conflict(
            asset_wrapper, tag_mod_report, match_results
        )

    if status == ClassificationStatus.UNCLASSIFIED:
        return _handle_unclassified_asset(asset_wrapper, tag_mod_report, album_decision)

    # Exhaustive pattern match - should never reach here
    raise NotImplementedError(
        f"Unhandled classification status: {status}. This indicates a logic error in ClassificationStatus enum."
    )
