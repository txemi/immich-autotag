import attrs
from typing import Dict, Iterator, Optional, TYPE_CHECKING
from immich_client import Client
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext

@attrs.define(auto_attribs=True, slots=True)
class AssetManager:
    client: Client
    _assets: Dict[str, AssetResponseWrapper] = attrs.field(factory=dict, init=False)

    def iter_assets(self, context: "ImmichContext", max_assets: Optional[int] = None) -> Iterator[AssetResponseWrapper]:
        """
        Itera sobre todos los assets, usando el generador original,
        y los va almacenando en la caché interna.
        """
        for asset in get_all_assets(context, max_assets=max_assets):
            self._assets[asset.id] = asset
            yield asset

    def get_asset(self, asset_id: str, context: "ImmichContext") -> Optional[AssetResponseWrapper]:
        """
        Devuelve un asset por su ID, usando la caché si está disponible,
        o pidiéndolo a la API y almacenándolo si no.
        """
        if asset_id in self._assets:
            return self._assets[asset_id]
        # Si no está, pedirlo a la API y envolverlo
        from immich_client.api.assets.get_asset import sync as get_asset_sync
        dto = get_asset_sync(client=self.client, id=asset_id)
        if dto is None:
            return None
        asset = AssetResponseWrapper.from_dto(dto, context)
        self._assets[asset_id] = asset
        return asset
