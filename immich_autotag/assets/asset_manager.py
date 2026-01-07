from typing import TYPE_CHECKING, Dict, Iterator, Optional, Union
from uuid import UUID

import attrs
from immich_client import Client
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.get_all_assets import get_all_assets

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True)
class AssetManager:

    client: Client
    _assets: Dict[UUID, AssetResponseWrapper] = attrs.field(factory=dict, init=False)

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
        for asset in get_all_assets(context, max_assets=max_assets, skip_n=skip_n):
            asset_uuid = UUID(asset.id)
            self._assets[asset_uuid] = asset
            yield asset

    @typechecked
    def get_asset(
        self, asset_id: UUID, context: "ImmichContext"
    ) -> Optional[AssetResponseWrapper]:
        """
        Returns an asset by its UUID, using the cache if available,
        or requesting it from the API and storing it if not.
        """
        if asset_id in self._assets:
            return self._assets[asset_id]
        # If not cached, request it from the API and wrap it
        from immich_client.api.assets import get_asset_info

        dto = get_asset_info.sync(id=str(asset_id), client=self.client)
        if dto is None:
            return None
        asset = AssetResponseWrapper.from_dto(dto, context)
        self._assets[asset_id] = asset
        return asset

    from immich_client.models.asset_response_dto import AssetResponseDto

    @typechecked
    def get_wrapper_for_asset(
        self, asset_dto: AssetResponseDto, context: "ImmichContext"
    ) -> AssetResponseWrapper:
        """
        Given an asset DTO, return the corresponding AssetResponseWrapper from cache or create it.
        """
        asset_uuid = UUID(asset_dto.id)
        if asset_uuid in self._assets:
            return self._assets[asset_uuid]
        wrapper = AssetResponseWrapper.from_dto(asset_dto, context)
        self._assets[asset_uuid] = wrapper
        return wrapper
