from typing import TYPE_CHECKING, Dict, Iterator, Optional
from uuid import UUID

import attrs
from immich_client import Client
from typeguard import typechecked

from immich_autotag.api.immich_proxy.assets import AssetResponseDto
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
        Añade diagnóstico de llamadas totales y IDs únicos.
        """
        if asset_id in self._assets:
            return self._assets[asset_id]
        asset = AssetResponseWrapper.from_api(asset_id, context)
        self._assets[asset_id] = asset
        return asset

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
        from immich_autotag.assets.asset_dto_state import AssetDtoType

        wrapper = AssetResponseWrapper.from_dto(asset_dto, context, AssetDtoType.FULL)
        self._assets[asset_uuid] = wrapper
        return wrapper
