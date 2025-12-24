from __future__ import annotations

from immich_client import Client
from immich_client.api.assets import get_asset_info
from typeguard import typechecked


@typechecked
def print_asset_details_with_tags(asset_id: str, client: Client) -> None:
    """Obtains and displays complete details of an asset, including tags."""
    asset = get_asset_info.sync(id=asset_id, client=client)
    tag_names = [tag.name for tag in asset.tags] if asset.tags else []
    print(
        f"Asset: {asset.original_file_name} | Tags: {', '.join(tag_names) if tag_names else '-'}"
    )
