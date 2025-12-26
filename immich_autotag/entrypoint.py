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

def run_main():
    client = Client(base_url=IMMICH_BASE_URL, headers={"x-api-key": API_KEY}, raise_on_unexpected_status=True)
    tag_collection = list_tags(client)
    albums_collection = list_albums(client)
    # Cargar duplicados
    duplicates_loader = DuplicatesLoader(client=client)
    duplicates_collection = duplicates_loader.load()
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
