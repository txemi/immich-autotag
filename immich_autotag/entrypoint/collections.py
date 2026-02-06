from __future__ import annotations

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.context.immich_context import ImmichContext


def init_collections_and_context(
    client_wrapper: ImmichClientWrapper,
) -> ImmichContext:
    """
    Initializes all collections and returns the ImmichContext instance.
    """
    # No need to build collections eagerly; just ensure context singleton exists
    context = ImmichContext.get_default_instance()
    return context


def force_full_album_loading(albums_collection: AlbumCollectionWrapper) -> None:
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

    albums_collection.ensure_all_full(perf_phase_tracker=perf_phase_tracker)


# New function: apply conversions to all assets before loading tags
def apply_conversions_to_all_assets_early(context: ImmichContext) -> None:
    """
    Iterates over all assets and applies the configured conversions as early as possible,
    before tags are accessed (lazy-load).
    """
    from immich_autotag.conversions.tag_conversions import TagConversions

    tag_conversions = TagConversions.from_config_manager()
    asset_manager = context.get_asset_manager()
    for asset in asset_manager.iter_assets(context):
        asset.apply_tag_conversions(tag_conversions=tag_conversions)
