from __future__ import annotations

from enum import Enum, auto
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
import attrs

# --- Detailed classification result ---
from typing import List



# ==================== USER-EDITABLE CONFIGURATION ====================
# All user configuration is now in a separate module for clarity and maintainability.
from immich_user_config import *

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# These variables are automatically derived and should not be edited by the user.

IMMICH_WEB_BASE_URL = f"http://{IMMICH_HOST}:{IMMICH_PORT}"
IMMICH_BASE_URL = f"{IMMICH_WEB_BASE_URL}/api"
IMMICH_PHOTO_PATH_TEMPLATE = "/photos/{id}"


@attrs.define(auto_attribs=True, slots=True)
class TagCollectionWrapper:

    tags: list[TagResponseDto]

    @typechecked
    def create_tag_if_not_exists(self, name: str, client) -> TagResponseDto:
        """
        Creates the tag in Immich if it doesn't exist and adds it to the local collection.
        Returns the corresponding TagResponseDto.
        """
        tag = self.find_by_name(name)
        if tag is not None:
            return tag
        from immich_client.api.tags import create_tag
        from immich_client.models.tag_create_dto import TagCreateDto

        tag_create = TagCreateDto(name=name)
        new_tag = create_tag.sync(client=client, body=tag_create)
        self.tags.append(new_tag)
        return new_tag

    @staticmethod
    @typechecked
    def from_api(client: Client) -> "TagCollectionWrapper":
        """
        Builds a TagCollectionWrapper instance by fetching tags from the Immich API.
        """
        from immich_client.api.tags import get_all_tags

        tags = get_all_tags.sync(client=client)
        return TagCollectionWrapper(tags=tags)

    @typechecked
    def find_by_name(self, name: str) -> TagResponseDto | None:
        for tag in self.tags:
            if tag.name == name:
                return tag
        return None

    @typechecked
    def __contains__(self, name: str) -> bool:
        return any(tag.name == name for tag in self.tags)

    @typechecked
    def __len__(self) -> int:
        return len(self.tags)

    @typechecked
    def __iter__(self):
        return iter(self.tags)


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class MatchClassificationResult:
    tags_matched: List[str]
    albums_matched: List[str]

    def any(self) -> bool:
        return bool(self.tags_matched or self.albums_matched)


# ==================== TAG MODIFICATION TRACE REPORT ====================

@attrs.define(auto_attribs=True, slots=True)
class TagModificationReport:
    report_path: str = "tag_modification_report.txt"
    batch_size: int = 1
    modifications: list = attrs.field(factory=list, init=False)
    _since_last_flush: int = attrs.field(default=0, init=False)
    _cleared_report: bool = attrs.field(default=False, init=False, repr=False)

    def add_modification(self, asset_id: str, asset_name: str, action: str, tag_name: str, user: str = None) -> None:
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


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AssetResponseWrapper:

    @typechecked
    def apply_tag_conversions(self, tag_conversions: list, tag_mod_report: 'TagModificationReport | None' = None):
        """
        For each tag conversion (origin -> destination), if the asset has the origin tag:
        - If it does not have the destination tag, add it and remove the origin tag.
        - If it has both, just remove the origin tag.
        All actions are logged in tag_mod_report if provided.
        """
        for conv in tag_conversions:
            origin = conv["origin"]
            dest = conv["destination"]
            has_origin = self.has_tag(origin)
            has_dest = self.has_tag(dest)
            if has_origin and not has_dest:
                try:
                    self.add_tag_by_name(dest, tag_mod_report=tag_mod_report)
                except Exception as e:
                    print(f"[WARN] Could not add tag '{dest}' to asset {self.id}: {e}")
                self.remove_tag_by_name(origin, tag_mod_report=tag_mod_report)
            elif has_origin and has_dest:
                self.remove_tag_by_name(origin, tag_mod_report=tag_mod_report)


    asset: AssetResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseDto)
    )
    context: ImmichContext = attrs.field()

    def __attrs_post_init__(self):
        if not isinstance(self.context, ImmichContext):
            raise TypeError(f"context debe ser ImmichContext, no {type(self.context)}")

    @typechecked
    def has_tag(self, tag_name: str) -> bool:
        """
        Returns True if the asset has the tag with that name (case-insensitive).
        """
        return (
            any(tag.name.lower() == tag_name.lower() for tag in self.asset.tags)
            if self.asset.tags
            else False
        )

    @typechecked
    def remove_tag_by_name(self, tag_name: str, verbose: bool = True, tag_mod_report: 'TagModificationReport | None' = None, user: str | None = None) -> bool:
        """
        Removes a tag from the asset by name using the Immich API if it has it.
        Returns True if removed, False if it didn't have it.
        """
        if not self.has_tag(tag_name):
            if verbose:
                print(f"[INFO] El asset.id={self.id} no tiene la etiqueta '{tag_name}'")
            return False
        from immich_client.api.tags import untag_assets
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        tag = self.context.tag_collection.find_by_name(tag_name)
        if tag is None:
            if verbose:
                print(
                    f"[WARN] Tag '{tag_name}' not found in global collection."
                )
            return False
        response = untag_assets.sync(
            id=tag.id, client=self.context.client, body=BulkIdsDto(ids=[self.id])
        )
        if verbose:
            print(
                f"[INFO] Removed tag '{tag_name}' from asset.id={self.id}. Response: {response}"
            )
        if tag_mod_report:
            tag_mod_report.add_modification(
                asset_id=self.id,
                asset_name=self.original_file_name,
                action="remove",
                tag_name=tag_name,
                user=user,
            )
        return True

    @typechecked
    def add_tag_by_name(
        self, tag_name: str, verbose: bool = False, info: bool = True, tag_mod_report: 'TagModificationReport | None' = None, user: str | None = None
    ) -> bool:
        """
        Adds a tag to the asset by name using the Immich API if it doesn't have it already.
        Returns True if added, raises exception if it already had it or if the tag doesn't exist.
        """
        from immich_client.api.tags import tag_assets
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        tag = self.context.tag_collection.find_by_name(tag_name)
        if tag is None:
            tag = self.context.tag_collection.create_tag_if_not_exists(
                tag_name, self.context.client
            )
        # Check if the asset already has the tag
        if self.has_tag(tag_name):
            raise ValueError(
                f"[INFO] Asset.id={self.id} already has tag '{tag_name}'"
            )
        # Call the correct endpoint to associate the tag with the asset
        if verbose:
            print(
                f"[DEBUG] Calling tag_assets.sync with tag_id={tag.id} and asset_id={self.id}"
            )
        response = tag_assets.sync(
            id=tag.id, client=self.context.client, body=BulkIdsDto(ids=[self.id])
        )
        if verbose:
            print(f"[DEBUG] Response tag_assets: {response}")
        # Request the asset again and check if the tag is applied
        updated_asset = get_asset_info.sync(id=self.id, client=self.context.client)
        if verbose:
            print(f"[DEBUG] Asset after tag_assets: {updated_asset}")
        tag_names = (
            [tag.name for tag in updated_asset.tags] if updated_asset.tags else []
        )
        if tag_name not in tag_names:
            raise RuntimeError(
                f"[ERROR] Tag '{tag_name}' doesn't appear in the asset after update. Current tags: {tag_names}"
            )
        if info:
            print(
                f"[INFO] Added tag '{tag_name}' to asset.id={self.id}. Current tags: {tag_names}"
            )
        if tag_mod_report:
            tag_mod_report.add_modification(
                asset_id=self.id,
                asset_name=self.original_file_name,
                action="add",
                tag_name=tag_name,
                user=user,
            )
        return True

    @typechecked
    def _get_current_tag_ids(self) -> list[str]:
        """Returns the IDs of the asset's current tags."""
        # No longer using getattr, accessing self.asset.tags directly
        return [t.id for t in self.asset.tags]

    @typechecked
    def get_album_names(self) -> list[str]:
        """
        Returns the names of the albums this asset belongs to.
        """
        return self.context.albums_collection.albums_for_asset(self.asset)

    @typechecked
    def get_tag_names(self) -> list[str]:
        """
        Returns the names of the tags associated with this asset.
        """
        return [tag.name for tag in self.asset.tags] if self.asset.tags else []

    @typechecked
    def is_asset_classified(self) -> bool:
        """
        Returns True if the asset meets any classification condition:
        - Has any of the tags in CLASSIFIED_TAGS.
        - Belongs to an album whose name matches ALBUM_PATTERN.
        """
        import re

        # Check tags
        asset_tags = self.get_tag_names()
        for tag in asset_tags:
            if tag.lower() in [t.lower() for t in CLASSIFIED_TAGS]:
                return True

        # Check albums
        album_names = self.get_album_names()
        for name in album_names:
            if re.match(ALBUM_PATTERN, name):
                return True

        return False

    @property
    def original_file_name(self) -> str:
        return self.asset.original_file_name

    @property
    def is_favorite(self) -> bool:
        return self.asset.is_favorite

    @property
    def created_at(self) -> str:
        return self.asset.created_at

    @property
    def id(self) -> str:
        return self.asset.id

    @property
    def original_path(self) -> str:
        return self.asset.original_path

    @typechecked
    def get_classification_match_detail(self) -> MatchClassificationResult:
        """
        Returns an object with the detail of the tags and albums that matched classification.
        """
        import re

        tags_matched = []
        albums_matched = []
        # Tags
        asset_tags = self.get_tag_names()
        for tag in asset_tags:
            if tag.lower() in [t.lower() for t in CLASSIFIED_TAGS]:
                tags_matched.append(tag)
        # Albums
        album_names = self.get_album_names()
        for name in album_names:
            if re.match(ALBUM_PATTERN, name):
                albums_matched.append(name)
        return MatchClassificationResult(
            tags_matched=tags_matched, albums_matched=albums_matched
        )

    @typechecked
    def check_unique_classification(self, fail_fast: bool = True) -> bool:
        """
        Checks if the asset is classified by more than one criterion (tag or album).
        Now considers conflict if the total number of matching tags and albums is greater than 1.
        If fail_fast is True (default), raises an exception. If False, logs a warning only.
        Returns True if there is a conflict (multiple criteria), False otherwise.
        """
        match_detail = self.get_classification_match_detail()
        n_matches = len(match_detail.tags_matched) + len(match_detail.albums_matched)
        if n_matches > 1:
            photo_url = (
                f"{IMMICH_WEB_BASE_URL}{IMMICH_PHOTO_PATH_TEMPLATE.format(id=self.id)}"
            )
            msg = f"[ERROR] Asset id={self.id} ({self.original_file_name}) is classified by more than one criterion: tags={match_detail.tags_matched}, albums={match_detail.albums_matched}\nLink: {photo_url}"
            if fail_fast:
                raise Exception(msg)
            else:
                print(msg)
            return True
        return False

    @typechecked
    def ensure_autotag_category_unknown(self, classified: bool, tag_mod_report: 'TagModificationReport | None' = None, user: str | None = None) -> None:
        """
        Add or remove the AUTOTAG_UNKNOWN_CATEGORY tag according to classification state.
        If not classified, add the tag only if not present. If classified and tag is present, remove it.
        Idempotent: does nothing if already in correct state.
        """
        tag_name = AUTOTAG_UNKNOWN_CATEGORY
        if not classified:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name, tag_mod_report=tag_mod_report, user=user)
                print(
                    f"[WARN] asset.id={self.id} ({self.original_file_name}) is not classified. Tagged as '{tag_name}'."
                )
        else:
            if self.has_tag(tag_name):
                print(
                    f"[INFO] Removing tag '{tag_name}' from asset.id={self.id} because it is now classified."
                )
                self.remove_tag_by_name(tag_name, tag_mod_report=tag_mod_report, user=user)

    @typechecked
    def ensure_autotag_conflict_category(self, conflict: bool, tag_mod_report: 'TagModificationReport | None' = None, user: str | None = None) -> None:
        """
        Adds or removes the AUTOTAG_CONFLICT_CATEGORY tag according to conflict state.
        If there is conflict, adds the tag if not present. If no conflict and tag is present, removes it.
        """
        tag_name = AUTOTAG_CONFLICT_CATEGORY
        if conflict:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name, tag_mod_report=tag_mod_report, user=user)
                print(
                    f"[WARN] asset.id={self.id} ({self.original_file_name}) is in classification conflict. Tagged as '{tag_name}'."
                )
        else:
            if self.has_tag(tag_name):
                print(
                    f"[INFO] Removing tag '{tag_name}' from asset.id={self.id} because it's no longer in conflict."
                )
                self.remove_tag_by_name(tag_name, tag_mod_report=tag_mod_report, user=user)

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
    albums: list[AlbumResponseWrapper]

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
    client: Client
    albums_collection: "AlbumCollectionWrapper"
    tag_collection: "TagCollectionWrapper"


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
            yield AssetResponseWrapper(asset=asset_full, context=context)
            count += 1
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
    # Autotag logic delegada a los métodos del wrapper, ahora pasando tag_mod_report
    asset_wrapper.ensure_autotag_category_unknown(classified, tag_mod_report=tag_mod_report)
    asset_wrapper.ensure_autotag_conflict_category(conflict, tag_mod_report=tag_mod_report)

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


@typechecked
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    count = 0
    tag_mod_report = TagModificationReport()

    for i, asset_wrapper in enumerate(get_all_assets(context, max_assets=max_assets)):
        # Tag conversion logic encapsulated in the asset
        asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)

        # Existing classification logic
        validate_and_update_asset_classification(
            asset_wrapper,
            tag_mod_report=tag_mod_report,
        )
        count += 1
        # For testing, you can limit the number of assets processed:
        # if i > 20:
        #     break

    print(f"Total assets: {count}")
    if len(tag_mod_report.modifications) > 0:
        tag_mod_report.print_summary()
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the actual minimum of assets
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
