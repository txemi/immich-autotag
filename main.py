from __future__ import annotations

import concurrent.futures
# --- Detailed classification result ---
from typing import Generator
# NOTE: With 'from __future__ import annotations' you can use types defined later in annotations,
# but for attrs validators the type must be defined before or validated in __attrs_post_init__.
from typing import TYPE_CHECKING

from immich_client import Client
from immich_client.api.albums import get_all_albums, get_album_info, update_album_info
from immich_client.api.assets import get_asset_info
from immich_client.api.search import search_assets
from immich_client.api.tags import get_all_tags
from immich_client.models import MetadataSearchDto
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.tag_response_dto import TagResponseDto
from immich_client.models.update_album_dto import UpdateAlbumDto
from typeguard import typechecked

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# Ahora centralizadas en immich_autotag/config.py
from immich_autotag.config import (
    IMMICH_BASE_URL,
    USE_THREADPOOL,
    MAX_WORKERS,
)
from immich_autotag.core.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.core.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.core.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.core.immich_context import ImmichContext
from immich_autotag.core.tag_collection_wrapper import TagCollectionWrapper
from immich_autotag.core.tag_modification_report import TagModificationReport
from immich_autotag.utils.asset_validation import validate_and_update_asset_classification
from immich_autotag.utils.helpers import print_perf
# ==================== USER-EDITABLE CONFIGURATION ====================
# All user configuration is now in a separate module for clarity and maintainability.
from immich_autotag.immich_user_config import *

from immich_autotag.utils.print_tags import print_tags

# ==================== TAG MODIFICATION TRACE REPORT ====================

if TYPE_CHECKING:
    from .ejemplo_immich_client import ImmichContext


@typechecked
def get_all_assets(
    context: "ImmichContext", max_assets: int | None = None
) -> "Generator[AssetResponseWrapper, None, None]":
    """
    Generator that produces AssetResponseWrapper one by one as they are obtained from the API.
    """
    page = 1
    count = 0
    while True:
        body = MetadataSearchDto(page=page)
        response = search_assets.sync_detailed(client=context.client, body=body)
        if response.status_code != 200:
            raise RuntimeError(f"Error: {response.status_code} - {response.content}")
        assets_page = response.parsed.assets.items
        for asset in assets_page:
            if max_assets is not None and count >= max_assets:
                return
            asset_full = get_asset_info.sync(id=asset.id, client=context.client)
            if asset_full is not None:
                yield AssetResponseWrapper(asset=asset_full, context=context)
                count += 1
            else:
                raise RuntimeError(
                    f"[ERROR] Could not load asset with id={asset.id}. get_asset_info returned None."
                )
        print(f"Page {page}: {len(assets_page)} assets (full info)")
        if (
            max_assets is not None and count >= max_assets
        ) or not response.parsed.assets.next_page:
            break
        page += 1


@typechecked
def list_albums(client: Client) -> AlbumCollectionWrapper:
    """
    Returns the collection of extended albums (wrappers) encapsulated in AlbumCollectionWrapper.
    """
    albums = get_all_albums.sync(client=client)
    albums_full: list[AlbumResponseWrapper] = []
    print("\nAlbums:")
    for album in albums:
        album_full = get_album_info.sync(id=album.id, client=client)
        n_assets = len(album_full.assets) if album_full.assets else 0
        print(f"- {album_full.album_name} (assets: {n_assets})")
        if album_full.album_name.startswith(" "):
            cleaned_name = album_full.album_name.strip()
            update_body = UpdateAlbumDto(album_name=cleaned_name)
            update_album_info.sync(
                id=album_full.id,
                client=client,
                body=update_body,
            )
            print(f"Renamed album '{album_full.album_name}' to '{cleaned_name}'")
            album_full.album_name = cleaned_name
        albums_full.append(AlbumResponseWrapper(album=album_full))
    print(f"Total albums: {len(albums_full)}\n")
    MIN_ALBUMS = 326
    if len(albums_full) < MIN_ALBUMS:
        raise Exception(
            f"ERROR: Unexpectedly low number of albums: {len(albums_full)} < {MIN_ALBUMS}"
        )
    return AlbumCollectionWrapper(albums=albums_full)


@typechecked
def list_tags(client: Client) -> TagCollectionWrapper:
    tag_collection = TagCollectionWrapper.from_api(client)
    print_tags(tag_collection.tags)
    return tag_collection


import concurrent.futures
from threading import Lock


@typechecked
def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    lock: Lock,
) -> None:
    # 1. Try album detection from folders (feature)
    detected_album = asset_wrapper.try_detect_album_from_folders()
    if detected_album:
        print(
            f"[ALBUM DETECTION] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' (from folders)"
        )
        # Check if the album already exists
        from immich_client.api.albums import (
            get_all_albums,
            create_album,
            add_assets_to_album,
        )
        from immich_client.models.albums_add_assets_dto import AlbumsAddAssetsDto

        client = asset_wrapper.context.client
        # Find album by exact name (case-sensitive)
        albums = get_all_albums.sync(client=client)
        album = next((a for a in albums if a.album_name == detected_album), None)
        if album is None:
            # Create album if it does not exist
            print(f"[ALBUM DETECTION] Creating album '{detected_album}'...")
            album = create_album.sync(client=client, album_name=detected_album)
        # Check if the asset is already in the album
        if asset_wrapper.id not in [a.id for a in getattr(album, "assets", []) or []]:
            print(
                f"[ALBUM DETECTION] Adding asset '{asset_wrapper.original_file_name}' to album '{detected_album}'..."
            )
            add_assets_to_album.sync(
                id=album.id,
                client=client,
                body=AlbumsAddAssetsDto(asset_ids=[asset_wrapper.id]),
            )
        else:
            print(
                f"[ALBUM DETECTION] Asset already belongs to album '{detected_album}'"
            )
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)
    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )
    with lock:
        tag_mod_report.flush()


@typechecked
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    import time
    from immich_client.api.server import get_server_statistics

    tag_mod_report = TagModificationReport()
    lock = Lock()
    count = 0
    N_LOG = 100  # Log frequency
    print(
        f"Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}..."
    )
    # Get total assets before processing
    try:
        stats = get_server_statistics.sync(client=context.client)
        total_assets = getattr(stats, "photos", 0) + getattr(stats, "videos", 0)
        print(
            f"[INFO] Total assets (photos + videos) reported by Immich: {total_assets}"
        )
    except Exception as e:
        print(f"[WARN] Could not get total assets from API: {e}")
        total_assets = None
    start_time = time.time()

    # print_perf now imported from helpers
    # Usage: print_perf(count, elapsed, total_assets)

    if USE_THREADPOOL:
        # Use thread pool regardless of MAX_WORKERS value
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for asset_wrapper in get_all_assets(context, max_assets=max_assets):
                future = executor.submit(
                    process_single_asset, asset_wrapper, tag_mod_report, lock
                )
                futures.append(future)
                count += 1
                if count % N_LOG == 0:
                    elapsed = time.time() - start_time
                    print_perf(count, elapsed)
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[ERROR] Asset processing failed: {e}")
    else:
        # Direct loop (sequential), no thread pool
        for asset_wrapper in get_all_assets(context, max_assets=max_assets):
            process_single_asset(asset_wrapper, tag_mod_report, lock)
            count += 1
            if count % N_LOG == 0:
                elapsed = time.time() - start_time
                print_perf(count, elapsed)
    total_time = time.time() - start_time
    print(f"Total assets: {count}")
    print(
        f"[PERF] Tiempo total: {total_time:.2f} s. Media por asset: {total_time/count if count else 0:.3f} s"
    )
    if len(tag_mod_report.modifications) > 0:
        tag_mod_report.print_summary()
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the real minimum number of assets
    if count < MIN_ASSETS:
        raise Exception(
            f"ERROR: Unexpectedly low number of assets: {count} < {MIN_ASSETS}"
        )


def main():
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


if __name__ == "__main__":
    main()
