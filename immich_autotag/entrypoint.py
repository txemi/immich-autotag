from __future__ import annotations
from immich_autotag.config.user import API_KEY
from immich_client import Client
from immich_autotag.config.internal_config import IMMICH_BASE_URL
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.assets.process_assets import process_assets
from immich_autotag.albums.list_albums import list_albums
from immich_autotag.tags.list_tags import list_tags
from immich_autotag.duplicates.duplicates_loader import DuplicatesLoader
from immich_autotag.assets.asset_manager import AssetManager
from typeguard import typechecked
from immich_autotag.duplicates.duplicate_collection_wrapper import DuplicateCollectionWrapper

@typechecked
def load_duplicates_collection(client) -> DuplicateCollectionWrapper:
    """
    Loads the duplicate collection from the Immich server and prints timing information.
    """
    import time
    print("[INFO] Requesting duplicates from Immich server... (this may take a while)")
    t0 = time.perf_counter()
    duplicates_loader = DuplicatesLoader(client=client)
    duplicates_collection = duplicates_loader.load()
    t1 = time.perf_counter()
    print(f"[INFO] Duplicates loaded in {t1-t0:.2f} s. Total groups: {len(duplicates_collection.groups_by_duplicate_id)}")
    return duplicates_collection
@typechecked
def run_main():
    client = Client(base_url=IMMICH_BASE_URL, headers={"x-api-key": API_KEY}, raise_on_unexpected_status=True)
    tag_collection = list_tags(client)
    albums_collection = list_albums(client)
    # Load duplicates
    duplicates_collection = load_duplicates_collection(client)
    asset_manager = AssetManager(client=client)
    context = ImmichContext(
        client=client,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
        duplicates_collection=duplicates_collection,
        asset_manager=asset_manager,
    )
    # You can change the max_assets value here or pass it as an external argument
    max_assets = None
    process_assets(context, max_assets=max_assets)
