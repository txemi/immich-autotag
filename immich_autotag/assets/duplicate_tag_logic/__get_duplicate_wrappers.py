from typeguard import typechecked
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from typeguard import typechecked
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

@typechecked
def get_duplicate_wrappers(asset_wrapper: AssetResponseWrapper) -> list[AssetResponseWrapper]:
    """
    Devuelve la lista de AssetResponseWrapper duplicados para el asset dado.
    """
    context = asset_wrapper.context
    return context.duplicates_collection.get_duplicate_asset_wrappers(
        asset_wrapper.duplicate_id_as_uuid, context.asset_manager, context
    )
