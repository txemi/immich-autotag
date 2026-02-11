from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


def deduplicate_assets_by_id(
    assets: list["AssetResponseWrapper"],
) -> list["AssetResponseWrapper"]:
    """
    Given a list of AssetResponseWrapper, return a list with unique assets by id (as string).
    """
    seen_ids: set[str] = set()
    unique_assets: list["AssetResponseWrapper"] = []
    for asset in assets:
        asset_id: str = str(asset.get_id())
        if asset_id not in seen_ids:
            seen_ids.add(asset_id)
            unique_assets.append(asset)
    return unique_assets
