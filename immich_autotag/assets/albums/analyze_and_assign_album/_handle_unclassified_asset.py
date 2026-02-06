"""Private handler for unclassified assets in album assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log

from .album_assignment_result import AlbumAssignmentResult

if TYPE_CHECKING:
    from immich_autotag.assets.albums.album_decision import AlbumDecision
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.report.modification_report import ModificationReport


@typechecked
def handle_unclassified_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    album_decision: "AlbumDecision",
) -> AlbumAssignmentResult:
    """
    Attempts to assign an album to an unclassified asset via detection or temporary album creation.
    """
    from immich_autotag.assets.albums._process_album_detection import (
        process_album_detection,
    )

    asset_name = asset_wrapper.get_original_file_name()

    # First, try to detect an existing album (from folders or duplicates)
    if album_decision.is_unique():
        detected_album = album_decision.get_unique()
        if detected_album:
            album_origin = album_decision.get_album_origin(detected_album)
            log(
                f"[ALBUM ASSIGNMENT] Asset '{asset_name}' will be assigned to album '{detected_album}' (origin: {album_origin}).",
                level=LogLevel.FOCUS,
            )
            process_album_detection(
                asset_wrapper=asset_wrapper,
                tag_mod_report=tag_mod_report,
                detected_album=detected_album,
                album_origin=album_origin,
            )
            return AlbumAssignmentResult.ASSIGNED_UNIQUE

    # If no unique album detected, try to create a temporary album
    from immich_autotag.assets.albums.temporary_manager.create_if_missing_classification import (
        create_album_if_missing_classification,
    )

    created_album = create_album_if_missing_classification(
        asset_wrapper, tag_mod_report
    )
    if created_album:
        return AlbumAssignmentResult.CREATED_TEMPORARY

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_name}' is not classified and no album could be assigned.",
        level=LogLevel.DEBUG,
    )
    return AlbumAssignmentResult.UNCLASSIFIED_NO_ALBUM
