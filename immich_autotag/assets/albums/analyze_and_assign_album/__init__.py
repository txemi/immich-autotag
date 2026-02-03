"""Album assignment logic for assets based on their classification status.

This module orchestrates the complete album assignment workflow for classified,
conflicted, and unclassified assets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._analyze_and_assign_album import _analyze_and_assign_album
from .album_assignment_report import AlbumAssignmentReport
from .album_assignment_result import AlbumAssignmentResult

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.report.modification_report import ModificationReport


def analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
) -> AlbumAssignmentReport:
    """Public API for album assignment analysis.

    Args:
        asset_wrapper: The asset to analyze and assign albums for
        tag_mod_report: The modification report from tag processing

    Returns:
        AlbumAssignmentReport with the result of the album assignment
    """
    return AlbumAssignmentReport.analyze(asset_wrapper, tag_mod_report)


__all__ = [
    "AlbumAssignmentReport",
    "AlbumAssignmentResult",
    "analyze_and_assign_album",
]
