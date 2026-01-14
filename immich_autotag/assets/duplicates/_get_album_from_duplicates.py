from __future__ import annotations

from typing import Dict
from uuid import UUID

from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.duplicates._duplicate_albums_info import DuplicateAssetsInfo


@typechecked
def get_duplicate_wrappers_info(
    asset_wrapper: "AssetResponseWrapper",
) -> DuplicateAssetsInfo:
    """
    For a given asset, if it is a duplicate, returns a DuplicateAssetsInfo object encapsulating the mapping from each duplicate AssetResponseWrapper (excluding itself).
    This allows for richer traceability and future extensibility.
    If there are no duplicates, returns an empty mapping.
    """
    result: Dict[UUID, AssetResponseWrapper] = {}
    duplicate_wrappers = asset_wrapper.get_duplicate_wrappers()
    for dup_wrapper in duplicate_wrappers:
        result[dup_wrapper.id_as_uuid] = dup_wrapper
    return DuplicateAssetsInfo(result)
