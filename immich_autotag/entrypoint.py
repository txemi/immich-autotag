from __future__ import annotations
from immich_autotag.config.user import API_KEY
from immich_client import Client
from immich_autotag.config.internal_config import IMMICH_BASE_URL
from immich_autotag.core.immich_context import ImmichContext
from immich_autotag.utils.process_assets import process_assets
from immich_autotag.utils.list_albums import list_albums
from immich_autotag.utils.list_tags import list_tags

def run_main():
    client = Client(base_url=IMMICH_BASE_URL, headers={"x-api-key": API_KEY})
    tag_collection = list_tags(client)
    albums_collection = list_albums(client)
    context = ImmichContext(
        client=client,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
    )
    # You can change the max_assets value here or pass it as an external argument
    max_assets = None
    process_assets(context, max_assets=max_assets)
