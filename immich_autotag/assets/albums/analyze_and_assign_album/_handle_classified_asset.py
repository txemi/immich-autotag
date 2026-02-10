"""Private handler for classified assets in album assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.assets.classification_validation_result import (
    ClassificationValidationResult,
)
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entries_list import ModificationEntriesList

from ._handle_unclassified_asset import AlbumAssignmentResultInfo
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
    cleanup_results = remove_asset_from_autotag_temporary_albums(
        asset_wrapper=asset_wrapper,
        temporary_albums=all_albums,
        tag_mod_report=tag_mod_report,
    )

    # cleanup_results is a ModificationEntriesList
    cleanup_mods = list(cleanup_results.entries())

    r2: ClassificationValidationResult = (
        asset_wrapper.validate_and_update_classification()
    )
    # r2.get_modifications() returns a ModificationEntriesList
    all_mods = cleanup_mods
    r2_mods = r2.get_modifications()
    if r2_mods is not None:
        all_mods.extend(r2_mods.entries())

    modifications = ModificationEntriesList(entries=all_mods) if all_mods else None

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.get_original_file_name()}' classified. "
        f"Temporary album cleanup and tags updated.",
        level=LogLevel.FOCUS,
    )

    return AlbumAssignmentResultInfo(AlbumAssignmentResult.CLASSIFIED, modifications)
