from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def validate_and_update_asset_classification(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: "ModificationReport" = None,
) -> tuple[bool, bool]:
    """
    Prints asset information, including the names of the albums it belongs to,
    using an album collection wrapper. Receives the global tag list to avoid double API call.
    If conflict_list is passed, adds the asset to the list if there is a classification conflict.
    """
    tag_names = asset_wrapper.get_tag_names()
    album_names = asset_wrapper.get_album_names()
    classified = asset_wrapper.is_asset_classified()  # Now returns bool

    # Check delegated to the wrapper method
    conflict = asset_wrapper.check_unique_classification(fail_fast=False)
    # Autotag logic delegated to the wrapper methods, now passing tag_mod_report
    asset_wrapper.ensure_autotag_category_unknown(classified)
    asset_wrapper.ensure_autotag_conflict_category(conflict)

    log(
        f"[CLASSIFICATION] Asset {asset_wrapper.id} | Name: {asset_wrapper.original_file_name} | Favorite: {asset_wrapper.is_favorite} | Tags: {', '.join(tag_names) if tag_names else '-'} | Albums: {', '.join(album_names) if album_names else '-'} | Classified: {classified} | Conflict: {conflict} | Date: {asset_wrapper.created_at} | original_path: {asset_wrapper.original_path}",
        level=LogLevel.FOCUS,
    )
    return bool(tag_names), bool(album_names)
