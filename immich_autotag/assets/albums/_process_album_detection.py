from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def _process_album_detection(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    detected_album: str,
    album_origin: str,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    # Log candidate album always at FOCUS level
    log(
        f"[ALBUM CHECK] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' (origin: {album_origin})",
        level=LogLevel.FOCUS,
    )

    client = asset_wrapper.context.client
    albums_collection = asset_wrapper.context.albums_collection
    album_wrapper = albums_collection.create_or_get_album_with_user(
        detected_album, client, tag_mod_report=tag_mod_report
    )
    album = album_wrapper.album
    if asset_wrapper.id not in [a.id for a in album.assets or []]:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' assigned to album '{detected_album}' (origin: {album_origin})",
            level=LogLevel.FOCUS,
        )
        album_wrapper.add_asset(asset_wrapper, client, tag_mod_report=tag_mod_report)
    else:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' already in album '{detected_album}' (origin: {album_origin}), no action taken.",
            level=LogLevel.FOCUS,
        )
