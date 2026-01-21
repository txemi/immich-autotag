from __future__ import annotations

from uuid import UUID

from immich_client.api.assets import get_asset_info
from typeguard import typechecked

from immich_autotag.types import ImmichClient


@typechecked
def print_asset_details_with_tags(asset_id: UUID, client: ImmichClient) -> None:
    """Obtains and displays complete details of an asset, including tags.

    Accepts either a `UUID` or a string representation and converts to `UUID`
    before calling the immich client to satisfy typed client signatures.
    """

    asset = get_asset_info.sync(id=asset_id, client=client)
    tag_names = [tag.name for tag in asset.tags] if asset.tags else []
    print(
        f"Asset: {asset.original_file_name} | Tags: {', '.join(tag_names) if tag_names else '-'}"
    )
