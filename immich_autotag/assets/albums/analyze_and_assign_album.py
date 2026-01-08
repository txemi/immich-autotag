from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums._process_album_detection import (
    _process_album_detection,
)
from immich_autotag.assets.albums.decide_album_for_asset import decide_album_for_asset
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    suppress_album_already_belongs_log: bool = True,
    fail_on_duplicate_album_conflict: bool = False,
) -> None:
    """
    Handles all logic related to analyzing potential albums for an asset, deciding assignment, and handling conflicts.
    """
    album_decision = decide_album_for_asset(asset_wrapper)
    # If there is an album conflict among duplicates, add the conflict tag; otherwise, remove it if present
    conflict = album_decision.has_conflict()
    duplicate_id = asset_wrapper.asset.duplicate_id
    # Apply the conflict tag logic to all duplicates
    all_wrappers = [asset_wrapper] + list(
        album_decision.duplicates_info.get_details().values()
    )
    for wrapper in all_wrappers:
        wrapper.ensure_autotag_duplicate_album_conflict(
            conflict, duplicate_id=duplicate_id
        )

    asset_name = asset_wrapper.original_file_name
    asset_id = asset_wrapper.id
    immich_url = asset_wrapper.get_immich_photo_url().geturl()
    if album_decision.is_unique():
        detected_album = album_decision.get_unique()
        if detected_album:
            album_origin = album_decision.get_album_origin(detected_album)
            log(
                f"[ALBUM ASSIGNMENT] Asset '{asset_name}' will be assigned to album '{detected_album}' (origin: {album_origin}).",
                level=LogLevel.FOCUS,
            )
            _process_album_detection(
                asset_wrapper,
                tag_mod_report,
                detected_album,
                album_origin,
                suppress_album_already_belongs_log=suppress_album_already_belongs_log,
            )
        else:
            log(
                f"[ALBUM ASSIGNMENT] No valid album found for asset '{asset_name}'. No assignment performed.",
                level=LogLevel.FOCUS,
            )
    elif conflict:
        albums_info = album_decision.duplicates_info
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' not assigned to any album due to conflict: multiple valid album options {album_decision.valid_albums()}\nSee asset: {immich_url}",
            level=LogLevel.FOCUS,
        )
        details = []
        for _, dup_wrapper in albums_info.get_details().items():
            albums = dup_wrapper.get_album_names()
            details.append(
                f"{dup_wrapper.get_link().geturl()} | file: {dup_wrapper.asset.original_file_name} | date: {dup_wrapper.asset.created_at} | albums: {albums or '[unavailable]'}"
            )
        if details:
            log(
                f"[ALBUM ASSIGNMENT] Duplicates of {asset_wrapper.uuid}:\n"
                + "\n".join(details),
                level=LogLevel.FOCUS,
            )
        if fail_on_duplicate_album_conflict:
            raise NotImplementedError(
                f"Ambiguous album assignment for asset {asset_id}: multiple valid albums {album_decision.valid_albums()}\nSee asset: {immich_url}\nDuplicates: {', '.join(details) if details else '-'}"
            )
        # No assignment performed due to ambiguity/conflict
        return
    else:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' was not assigned to any album. No valid or conflicting options found.",
            level=LogLevel.FOCUS,
        )
