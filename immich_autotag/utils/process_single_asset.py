from __future__ import annotations

from threading import Lock

from typeguard import typechecked

from immich_autotag.core.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.core.tag_modification_report import TagModificationReport
from immich_autotag.utils.asset_validation import validate_and_update_asset_classification
from immich_autotag.immich_user_config import TAG_CONVERSIONS


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    lock: Lock,
) -> None:
    # 1. Try album detection from folders (feature)
    detected_album = asset_wrapper.try_detect_album_from_folders()
    if detected_album:
        print(
            f"[ALBUM DETECTION] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' (from folders)"
        )
        # Check if the album already exists
        from immich_client.api.albums import (
            get_all_albums,
            create_album,
            add_assets_to_album,
        )
        from immich_client.models.albums_add_assets_dto import AlbumsAddAssetsDto

        client = asset_wrapper.context.client
        # Find album by exact name (case-sensitive)
        albums = get_all_albums.sync(client=client)
        album = next((a for a in albums if a.album_name == detected_album), None)
        if album is None:
            # Create album if it does not exist
            print(f"[ALBUM DETECTION] Creating album '{detected_album}'...")
            album = create_album.sync(client=client, album_name=detected_album)
        # Check if the asset is already in the album
        if asset_wrapper.id not in [a.id for a in getattr(album, "assets", []) or []]:
            print(
                f"[ALBUM DETECTION] Adding asset '{asset_wrapper.original_file_name}' to album '{detected_album}'..."
            )
            add_assets_to_album.sync(
                id=album.id,
                client=client,
                body=AlbumsAddAssetsDto(asset_ids=[asset_wrapper.id]),
            )
        else:
            print(
                f"[ALBUM DETECTION] Asset already belongs to album '{detected_album}'"
            )
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )
    with lock:
        tag_mod_report.flush()
