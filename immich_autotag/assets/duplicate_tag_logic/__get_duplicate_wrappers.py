from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@typechecked
def get_duplicate_wrappers(
    asset_wrapper: AssetResponseWrapper,
) -> list[AssetResponseWrapper]:
    """
    Returns the list of duplicate AssetResponseWrapper for the given asset.
    """
    context = asset_wrapper.get_context()
    return context.get_duplicates_collection().get_duplicate_asset_wrappers(
        asset_wrapper.get_duplicate_id_as_uuid(), context.get_asset_manager(), context
    )
