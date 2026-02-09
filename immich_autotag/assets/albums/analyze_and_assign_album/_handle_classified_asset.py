"""Private handler for classified assets in album assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.assets.classification_validation_result import (
    ClassificationValidationResult,
)
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log

from .album_assignment_result import AlbumAssignmentResult

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.report.modification_report import ModificationReport


@typechecked
def handle_classified_asset(
    asset_wrapper: "AssetResponseWrapper", tag_mod_report: "ModificationReport"
) -> "AlbumAssignmentResultInfo":
    """
    Cleans up temporary albums and updates tags for a classified asset.
    """
    from immich_autotag.assets.albums.temporary_manager.cleanup import (
        remove_asset_from_autotag_temporary_albums,
    )

    all_albums = list(
        asset_wrapper.get_context()
        .get_albums_collection()
        .albums_wrappers_for_asset_wrapper(asset_wrapper)
    )
    result = remove_asset_from_autotag_temporary_albums(
        asset_wrapper=asset_wrapper,
        temporary_albums=all_albums,
        tag_mod_report=tag_mod_report,
    )
    # Remove 'unknown' tag if present and update classification tags
    r2: ClassificationValidationResult = (
        asset_wrapper.validate_and_update_classification()
    )

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.get_original_file_name()}' classified. "
        f"Temporary album cleanup and tags updated.",
        level=LogLevel.FOCUS,
    )

    from ._handle_unclassified_asset import AlbumAssignmentResultInfo

    return AlbumAssignmentResultInfo(AlbumAssignmentResult.CLASSIFIED, result)
