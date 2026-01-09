from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums.album_decision import AlbumDecision
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.duplicates._get_album_from_duplicates import (
    get_album_from_duplicates,
)


@typechecked
def decide_album_for_asset(asset_wrapper: "AssetResponseWrapper") -> AlbumDecision:
    """
    Returns an AlbumDecision object with all relevant information to decide the album.
    """
    albums_info = get_album_from_duplicates(asset_wrapper)
    detected_album = asset_wrapper.try_detect_album_from_folders()
    return AlbumDecision(duplicates_info=albums_info, album_from_folder=detected_album)
