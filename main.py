from __future__ import annotations

import datetime

from immich_client.models.update_album_dto import UpdateAlbumDto
from typeguard import typechecked
from immich_client.api.assets import get_asset_info


from immich_client import Client
from immich_client.api.search import search_assets
from immich_client.api.albums import get_all_albums, get_album_info, update_album_info
from immich_client.api.tags import get_all_tags
from immich_client.models.tag_response_dto import TagResponseDto
from immich_client.models import MetadataSearchDto
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.album_response_dto import AlbumResponseDto

from immich_autotag.core.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.utils.helpers import print_perf
import concurrent.futures
import attrs
from pathlib import Path

# --- Detailed classification result ---
from typing import Generator
from immich_autotag.core.tag_collection_wrapper import TagCollectionWrapper


# ==================== USER-EDITABLE CONFIGURATION ====================
# All user configuration is now in a separate module for clarity and maintainability.
from immich_user_config import *

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# These variables are automatically derived and should not be edited by the user.

IMMICH_WEB_BASE_URL = f"http://{IMMICH_HOST}:{IMMICH_PORT}"
IMMICH_BASE_URL = f"{IMMICH_WEB_BASE_URL}/api"
IMMICH_PHOTO_PATH_TEMPLATE = "/photos/{id}"
# ==================== LOG CONFIGURATION ====================
PRINT_ASSET_DETAILS = False  # Set to True to enable detailed per-asset logging
# Control whether to use ThreadPoolExecutor for asset processing, regardless of MAX_WORKERS value.
# If False, always use direct loop (sequential). If True, use thread pool even for MAX_WORKERS=1.
USE_THREADPOOL = True  # Set to True to force thread pool usage, False for direct loop
# Sequential mode is usually faster for this workload, but you can experiment with USE_THREADPOOL for benchmarking.
MAX_WORKERS = 1  # Set to 1 for sequential processing (recommended for best performance in this environment)






# ==================== TAG MODIFICATION TRACE REPORT ====================


@attrs.define(auto_attribs=True, slots=True)
class TagModificationReport:
    import os, datetime as dt

    log_dir: str = attrs.field(
        default="logs", validator=attrs.validators.instance_of(str)
    )
    report_path: str = attrs.field(
        default=f"logs/tag_modification_report_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}.txt",
        validator=attrs.validators.instance_of(str),
    )
    batch_size: int = attrs.field(
        default=1, validator=attrs.validators.instance_of(int)
    )
    modifications: list = attrs.field(
        factory=list, init=False, validator=attrs.validators.instance_of(list)
    )
    _since_last_flush: int = attrs.field(
        default=0, init=False, validator=attrs.validators.instance_of(int)
    )
    _cleared_report: bool = attrs.field(
        default=False,
        init=False,
        repr=False,
        validator=attrs.validators.instance_of(bool),
    )

    def add_modification(
        self,
        asset_id: str,
        asset_name: str,
        action: str,
        tag_name: str,
        user: str = None,
    ) -> None:
        """
        Registers a tag modification (add/remove) for an asset.
        """
        if not self._cleared_report:
            try:
                with open(self.report_path, "w", encoding="utf-8") as f:
                    pass  # Truncate the file
            except Exception as e:
                print(f"[WARN] Could not clear the tag modification report: {e}")
            self._cleared_report = True
        # Build photo link
        photo_link = f"{IMMICH_WEB_BASE_URL}/photos/{asset_id}"
        entry = {
            "datetime": datetime.datetime.now().isoformat(),
            "asset_id": asset_id,
            "asset_name": asset_name,
            "action": action,  # 'add' or 'remove'
            "tag_name": tag_name,
            "user": user,
            "photo_link": photo_link,
        }
        self.modifications.append(entry)
        self._since_last_flush += 1
        if self._since_last_flush >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        """Flushes the report to file (append)."""
        if not self.modifications or self._since_last_flush == 0:
            return
        with open(self.report_path, "a", encoding="utf-8") as f:
            for entry in self.modifications[-self._since_last_flush :]:
                f.write(
                    f"{entry['datetime']} | asset_id={entry['asset_id']} | name={entry['asset_name']} | action={entry['action']} | tag={entry['tag_name']} | link={entry['photo_link']}"
                )
                if entry["user"]:
                    f.write(f" | user={entry['user']}")
                f.write("\n")
        self._since_last_flush = 0

    def print_summary(self) -> None:
        print("\n[SUMMARY] Tag modifications:")
        for entry in self.modifications:
            print(
                f"{entry['datetime']} | asset_id={entry['asset_id']} | name={entry['asset_name']} | action={entry['action']} | tag={entry['tag_name']} | link={entry['photo_link']}"
                + (f" | user={entry['user']}" if entry["user"] else "")
            )
        print(f"Total modifications: {len(self.modifications)}")


# NOTE: With 'from __future__ import annotations' you can use types defined later in annotations,
# but for attrs validators the type must be defined before or validated in __attrs_post_init__.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ejemplo_immich_client import ImmichContext

import attrs


@attrs.define(auto_attribs=True, slots=True)
class AlbumFolderAnalyzer:
    original_path: Path = attrs.field(validator=attrs.validators.instance_of(Path))
    folders: list = attrs.field(
        init=False, validator=attrs.validators.instance_of(list)
    )
    date_pattern: str = attrs.field(
        init=False,
        default=r"^\d{4}-\d{2}-\d{2}$",
        validator=attrs.validators.instance_of(str),
    )

    def __attrs_post_init__(self):
        import re

        # Convert to Path if not already
        path = (
            self.original_path
            if isinstance(self.original_path, Path)
            else Path(self.original_path)
        )
        # Get all parts except root
        folders = [
            part
            for part in path.parts
            if part not in (path.root, path.anchor, ".", "..", "")
        ]
        # If the last component looks like a file (has an extension), remove it
        if folders and re.search(r"\.[a-zA-Z0-9]{2,5}$", folders[-1]):
            folders = folders[:-1]
        self.folders = folders

    def date_folder_indices(self):
        import re

        return [
            i for i, f in enumerate(self.folders) if re.fullmatch(self.date_pattern, f)
        ]

    @typechecked
    def num_date_folders(self):
        return len(self.date_folder_indices())

    @typechecked
    def is_date_in_last_position(self):
        idxs = self.date_folder_indices()
        return len(idxs) == 1 and idxs[0] == len(self.folders) - 1

    @typechecked
    def is_date_in_penultimate_position(self):
        idxs = self.date_folder_indices()
        return len(idxs) == 1 and idxs[0] == len(self.folders) - 2

    @typechecked
    def get_album_name(self):
        import re

        # 0 date folders: look for folder starting with date (but not only date)
        if self.num_date_folders() == 0:
            date_prefix_pattern = r"^\d{4}-\d{2}-\d{2}"
            for f in self.folders:
                if re.match(date_prefix_pattern, f) and not re.fullmatch(
                    self.date_pattern, f
                ):
                    if len(f) < 10:
                        raise NotImplementedError(
                            f"Detected album name is suspiciously short: '{f}'"
                        )
                    return f
            return None
        # >1 date folders: ambiguous, not supported
        if self.num_date_folders() > 1:
            idxs = self.date_folder_indices()
            raise NotImplementedError(
                f"Multiple candidate folders for album detection: {[self.folders[i] for i in idxs]}"
            )
        # 1 date folder
        idx = self.date_folder_indices()[0]
        if idx == len(self.folders) - 1:
            # Date folder is the last (containing folder): ignore
            return None
        if idx == len(self.folders) - 2:
            # Date folder is penultimate: concatenate with last
            album_name = f"{self.folders[idx]} {self.folders[idx+1]}"
            if len(album_name) < 10:
                raise NotImplementedError(
                    f"Detected album name is suspiciously short: '{album_name}'"
                )
            return album_name
        # Date folder in other position: not supported for now
        return None


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumResponseWrapper:
    album: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )

    @typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        """Returns True if the asset belongs to this album."""
        if self.album.assets:
            return any(a.id == asset.id for a in self.album.assets)
        return False

    @typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        """
        Returns the album's assets wrapped in AssetResponseWrapper.
        """
        return (
            [AssetResponseWrapper(asset=a, context=context) for a in self.album.assets]
            if self.album.assets
            else []
        )


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumCollectionWrapper:
    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    @typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[str]:
        """Returns the names of the albums the asset belongs to."""
        album_names = []
        for album_wrapper in self.albums:
            if album_wrapper.has_asset(asset):
                album_names.append(album_wrapper.album.album_name)
        return album_names


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ImmichContext:
    client: Client = attrs.field(validator=attrs.validators.instance_of(Client))
    albums_collection: "AlbumCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
    tag_collection: "TagCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )


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
def validate_and_update_asset_classification(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: "TagModificationReport" = None,
) -> tuple[bool, bool]:
    """
    Prints asset information, including the names of the albums it belongs to,
    using an album collection wrapper. Receives the global tag list to avoid double API call.
    If conflict_list is passed, adds the asset to the list if there is a classification conflict.
    """

    tag_names = asset_wrapper.get_tag_names()
    album_names = asset_wrapper.get_album_names()
    classified = asset_wrapper.is_asset_classified()  # Now returns bool

    # Check delegated to the wrapper method
    conflict = asset_wrapper.check_unique_classification(fail_fast=False)
    # Autotag logic delegated to the wrapper methods, now passing tag_mod_report
    asset_wrapper.ensure_autotag_category_unknown(
        classified, tag_mod_report=tag_mod_report
    )
    asset_wrapper.ensure_autotag_conflict_category(
        conflict, tag_mod_report=tag_mod_report
    )

    if PRINT_ASSET_DETAILS:
        print(
            f"ID: {asset_wrapper.id} | Name: {asset_wrapper.original_file_name} | Favorite: {asset_wrapper.is_favorite} | Tags: {', '.join(tag_names) if tag_names else '-'} | Albums: {', '.join(album_names) if album_names else '-'} | Classified: {classified} | Date: {asset_wrapper.created_at} | original_path: {asset_wrapper.original_path}"
        )
    return bool(tag_names), bool(album_names)


@typechecked
def print_asset_details_with_tags(asset_id: str, client: Client) -> None:
    """Obtains and displays complete details of an asset, including tags."""
    asset = get_asset_info.sync(id=asset_id, client=client)
    tag_names = [tag.name for tag in asset.tags] if asset.tags else []
    print(
        f"Asset: {asset.original_file_name} | Tags: {', '.join(tag_names) if tag_names else '-'}"
    )


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
def print_tags(tags: list[TagResponseDto]) -> None:
    print("Tags:")
    for tag in tags:
        print(f"- {tag.name}")
    print(f"Total tags: {len(tags)}\n")
    MIN_TAGS = 57
    if len(tags) < MIN_TAGS:
        raise Exception(
            f"ERROR: Unexpectedly low number of tags: {len(tags)} < {MIN_TAGS}"
        )


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
