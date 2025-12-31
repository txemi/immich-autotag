from typing import TYPE_CHECKING, Dict, Iterator, Optional, Union
from uuid import UUID

import attrs
from immich_client import Client

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.get_all_assets import get_all_assets

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True)
class AssetManager:
    client: Client
    _assets: Dict[UUID, AssetResponseWrapper] = attrs.field(factory=dict, init=False)

    def iter_assets(
        self, context: "ImmichContext", max_assets: Optional[int] = None
    ) -> Iterator[AssetResponseWrapper]:
        """
        Itera sobre todos los assets, usando el generador original,
        y los va almacenando en la caché interna.
        """
        for asset in get_all_assets(context, max_assets=max_assets):
            asset_uuid = UUID(asset.id)  # Si falla, que lance
            self._assets[asset_uuid] = asset
            yield asset

    def get_asset(
        self, asset_id: Union[str, UUID], context: "ImmichContext"
    ) -> Optional[AssetResponseWrapper]:
        """
        Devuelve un asset por su ID, usando la caché si está disponible,
        o pidiéndolo a la API y almacenándolo si no.
        """
        asset_uuid = (
            UUID(asset_id) if isinstance(asset_id, str) else asset_id
        )  # Si falla, que lance
        if asset_uuid in self._assets:
            return self._assets[asset_uuid]
        # Si no está, pedirlo a la API y envolverlo
        from immich_client.api.assets import get_asset_info

        dto = get_asset_info.sync(id=str(asset_uuid), client=self.client)
        if dto is None:
            return None
        asset = AssetResponseWrapper.from_dto(dto, context)
        self._assets[asset_uuid] = asset
        return asset
