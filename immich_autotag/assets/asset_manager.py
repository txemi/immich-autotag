from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Optional

import attrs
from typeguard import typechecked

from immich_autotag.api.immich_proxy.assets import AssetResponseDto
from immich_autotag.api.immich_proxy.types import Client
from immich_autotag.assets.asset_cache_entry import AssetCacheEntry
from immich_autotag.assets.asset_dto_state import AssetDtoType
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.config.internal_config import KEEP_ASSETS_IN_MEMORY
from immich_autotag.types.uuid_wrappers import AssetUUID

# Removed import: AssetCacheEntry is only used internally in AssetResponseWrapper

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True)
class AssetManager:

    client: Client
    # If not kept in memory, _assets will be None
    _assets: Optional[dict[AssetUUID, AssetResponseWrapper]] = attrs.field(
        default=None, init=False
    )
    _keep_assets_in_memory: bool = attrs.field(
        default=KEEP_ASSETS_IN_MEMORY, init=False
    )

    def __attrs_post_init__(self):
        self._keep_assets_in_memory = KEEP_ASSETS_IN_MEMORY
        if self._keep_assets_in_memory:
            self._assets = {}
        else:
            self._assets = None

    @typechecked
    def iter_assets(
        self,
        context: "ImmichContext",
        max_assets: Optional[int] = None,
        skip_n: int = 0,
    ) -> Iterator[AssetResponseWrapper]:
        """
        Iterates over all assets, using the original generator, and stores them in the internal cache.
        Supports skipping the first `skip_n` assets efficiently.
        """
        from immich_autotag.assets.get_all_assets import get_all_assets

        for asset in get_all_assets(context, max_assets=max_assets, skip_n=skip_n):
            if not isinstance(asset, AssetResponseWrapper):
                raise RuntimeError(f"Expected AssetResponseWrapper, got {type(asset)}")
            asset_uuid = asset.get_id()
            if self._assets is not None:
                self._assets[asset_uuid] = asset
            yield asset

    @typechecked
    def get_asset(
        self, asset_id: "AssetUUID", context: "ImmichContext"
    ) -> Optional[AssetResponseWrapper]:
        """
        Returns an asset by its AssetUUID, using the cache if available,
        or requesting it from the API and storing it if not.
        First checks the in-memory cache, then disk, and finally the API.
        """
        if self._assets is not None and asset_id in self._assets:
            return self._assets[asset_id]

        asset = AssetResponseWrapper.from_id(asset_id, context)
        if self._assets is not None:
            self._assets[asset_id] = asset
        return asset

    @typechecked
    def get_wrapper_for_asset_dto(
        self,
        *,
        asset_dto: AssetResponseDto,
        dto_type: AssetDtoType,
        context: "ImmichContext",
    ) -> AssetResponseWrapper:
        """
        Given an asset DTO, return the corresponding AssetResponseWrapper from cache or create it.
        """
        if dto_type not in (AssetDtoType.ALBUM, AssetDtoType.SEARCH):
            raise ValueError(f"Unsupported dto_type {dto_type} for album asset DTOs")
        asset_uuid = AssetUUID.from_string(asset_dto.id)
        if self._assets is not None and asset_uuid in self._assets:
            return self._assets[asset_uuid]

        entry = AssetCacheEntry._from_dto_entry(dto=asset_dto, dto_type=dto_type)
        wrapper = AssetResponseWrapper(context, entry)
        if self._assets is not None:
            self._assets[asset_uuid] = wrapper
        return wrapper
