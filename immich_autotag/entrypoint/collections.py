from __future__ import annotations

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.load_duplicates_collection import (
    load_duplicates_collection,
)
from immich_autotag.tags.list_tags import list_tags


def init_collections_and_context(
    client_wrapper: ImmichClientWrapper,
) -> ImmichContext:
    """
    Initializes all collections and returns the ImmichContext instance.
    """
    client = client_wrapper.get_client()
    tag_collection = list_tags(client)
    albums_collection = AlbumCollectionWrapper.from_client()
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

    perf_phase_tracker.mark(phase="lazy", event="start")
    albums_collection.log_lazy_load_timing()
    perf_phase_tracker.mark(phase="lazy", event="end")
    duplicates_collection = load_duplicates_collection(client)
    asset_manager = AssetManager(client=client)  # type: ignore
    context = ImmichContext.create_default_instance(
        client=client_wrapper,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
        duplicates_collection=duplicates_collection,
        asset_manager=asset_manager,
    )
    return context


def force_full_album_loading(albums_collection: AlbumCollectionWrapper) -> None:
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

    albums_collection.ensure_all_full(perf_phase_tracker=perf_phase_tracker)


# Nueva función: aplicar conversiones a todos los assets antes de cargar tags
def apply_conversions_to_all_assets_early(context: ImmichContext) -> None:
    """
    Itera por todos los assets y aplica las conversiones configuradas lo antes posible,
    antes de que se acceda a los tags (lazy-load).
    """
    from immich_autotag.conversions.tag_conversions import TagConversions
    tag_conversions = TagConversions.from_config_manager()
    asset_manager = context.get_asset_manager()
    for asset in asset_manager.iter_assets(context):
        asset.apply_tag_conversions(tag_conversions=tag_conversions)
