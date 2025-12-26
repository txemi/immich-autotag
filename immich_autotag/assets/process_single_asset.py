from __future__ import annotations

from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.tags.tag_modification_report import TagModificationReport
from immich_autotag.assets.asset_validation import validate_and_update_asset_classification
from immich_autotag.config.user import TAG_CONVERSIONS


@typechecked

def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    lock: Lock,
) -> None:
    detected_album = asset_wrapper.try_detect_album_from_folders()
    if detected_album:
        asset_wrapper.try_detect_album_from_folders()
        _process_album_detection(asset_wrapper, tag_mod_report, detected_album)
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )
    with lock:
        tag_mod_report.flush()

@typechecked
def _process_album_detection(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    detected_album: str,
) -> None:
    print(
        f"[ALBUM DETECTION] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' (from folders)"
    )
    from immich_client.api.albums import add_assets_to_album
    from immich_client.models.albums_add_assets_dto import AlbumsAddAssetsDto

    client = asset_wrapper.context.client
    albums_collection = asset_wrapper.context.albums_collection
    album_wrapper = albums_collection.create_or_get_album_with_user(
        detected_album, client, tag_mod_report=tag_mod_report
    )
    album = album_wrapper.album
    if asset_wrapper.id not in [a.id for a in album.assets or []]:
        print(
            f"[ALBUM DETECTION] Adding asset '{asset_wrapper.original_file_name}' to album '{detected_album}'..."
        )
        # todo: viendo la llamada de abajo el codigo parece que recibe un BulkIdsDto y no un AlbumsAddAssetsDto, puedes revisarlo?
        add_assets_to_album.sync(
            id=album.id,
            client=client,
            body=BulkIdsDto(ids=[asset_wrapper.id]),
        )
        add_assets_to_album.sync(
            id=album.id,
            client=client,
            body=AlbumsAddAssetsDto(album_ids=[album.id], asset_ids=[asset_wrapper.id]),
        )
        tag_mod_report.add_assignment_modification(
            action="assign",
            asset_id=asset_wrapper.id,
            asset_name=asset_wrapper.original_file_name,
            album_id=album.id,
            album_name=detected_album,
        )
    else:
        print(
            f"[ALBUM DETECTION] Asset already belongs to album '{detected_album}'"
        )
