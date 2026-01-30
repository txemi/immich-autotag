from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.asset_uuid import AssetUUID
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.types.client_types import ImmichClient


@typechecked
def print_asset_details_with_tags(asset_id: AssetUUID, client: ImmichClient) -> None:
    """Obtains and displays complete details of an asset, including tags.

    Accepts either a `UUID` or a string representation and converts to `UUID`
    before calling the immich client to satisfy typed client signatures.
    """

    # Get the global context (singleton)
    context = ImmichContext.get_default_instance()

    asset_wrapper = context.asset_manager.get_asset(asset_id, context)
    if asset_wrapper is None:
        raise RuntimeError(f"Asset with ID {asset_id} not found.")
    tag_list = asset_wrapper.get_tags()
    tag_names = [tag.get_name() for tag in tag_list] if tag_list else []
    print(
        f"Asset: {asset_wrapper.asset.get_original_file_name()} | Tags: {', '.join(tag_names) if tag_names else '-'}"
    )
