from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def process_album_detection(
    *,
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    detected_album: str,
    album_origin: str,
) -> None:
    # Log candidate album always at FOCUS level
    log(
        f"[ALBUM CHECK] Asset '{asset_wrapper.get_original_file_name()}' "
        f"candidate album: '{detected_album}' (origin: {album_origin})",
        level=LogLevel.FOCUS,
    )

    context = asset_wrapper.get_context()
    client = context.get_client_wrapper().get_client()
    albums_collection = context.get_albums_collection()
    album_wrapper = albums_collection.create_or_get_album_with_user(
        album_name=detected_album,
        client=client,
        tag_mod_report=tag_mod_report,
    )
    # Check membership using explicit get_asset_ids() to avoid ambiguous property behavior
    if asset_wrapper.get_id() not in album_wrapper.get_asset_ids():
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.get_original_file_name()}' "
            f"assigned to album '{detected_album}' (origin: {album_origin})",
            level=LogLevel.FOCUS,
        )
        album_wrapper.add_asset(
            asset_wrapper=asset_wrapper,
            client=client,
            tag_mod_report=tag_mod_report,
        )
    else:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.get_original_file_name()}' "
            f"already in album '{detected_album}' (origin: {album_origin}), no action taken.",
            level=LogLevel.FOCUS,
        )
