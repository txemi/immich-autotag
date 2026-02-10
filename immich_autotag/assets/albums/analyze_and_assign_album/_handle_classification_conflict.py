"""Private handler for classification conflicts in album assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_kind import ModificationKind

from .album_assignment_result import AlbumAssignmentResult
from ._handle_unclassified_asset import AlbumAssignmentResultInfo
from immich_autotag.report.modification_entries_list import ModificationEntriesList

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.classification.match_result_list import MatchResultList
    from immich_autotag.report.modification_report import ModificationReport


@typechecked
def handle_classification_conflict(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    match_results: "MatchResultList",
) -> AlbumAssignmentResultInfo:
    """
    Handles assets that match multiple classification rules by removing them from temporary albums
    and reporting the conflict.
    """
    from immich_autotag.assets.albums.temporary_manager.cleanup import (
        remove_asset_from_autotag_temporary_albums,
    )

    all_albums = list(
        asset_wrapper.get_context()
        .get_albums_collection()
        .albums_wrappers_for_asset_wrapper(asset_wrapper)
    )
    report_entry = remove_asset_from_autotag_temporary_albums(
        asset_wrapper=asset_wrapper,
        temporary_albums=all_albums,
        tag_mod_report=tag_mod_report,
    )
    modifications = None
    if report_entry is not None:
        modifications = ModificationEntriesList(entries=[report_entry])

    num_rules_matched = len(list(match_results.rules()))
    asset_name = asset_wrapper.get_original_file_name()
    asset_id = asset_wrapper.get_id()
    immich_url = asset_wrapper.get_immich_photo_url().geturl()

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_name}' ({asset_id}) matched {num_rules_matched} classification rules. "
        f"Classification conflict: removed from temporary album if it was there.\nSee asset: {immich_url}",
        level=LogLevel.ERROR,
    )

    conflict_entry: ModificationEntry = tag_mod_report.add_modification(
        kind=ModificationKind.CLASSIFICATION_CONFLICT,
        asset_wrapper=asset_wrapper,
        extra={
            "reason": "multiple_rules_matched",
            "num_rules": num_rules_matched,
            "asset_name": asset_name,
            "asset_id": asset_id,
        },
    )
    # Add the conflict entry to the modifications list
    if modifications is None:
        modifications = ModificationEntriesList(entries=[conflict_entry])
    else:
        modifications = modifications.append(conflict_entry)
    return AlbumAssignmentResultInfo(AlbumAssignmentResult.CONFLICT, modifications)
