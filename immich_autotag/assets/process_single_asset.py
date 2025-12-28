from __future__ import annotations
from typing import Set, Dict, List

from threading import Lock

from immich_client.models.bulk_ids_dto import BulkIdsDto
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.tags.tag_modification_report import TagModificationReport

from immich_autotag.assets.asset_validation import validate_and_update_asset_classification
from immich_autotag.config.user import TAG_CONVERSIONS, ALBUM_PATTERN
from immich_autotag.tags.modification_kind import ModificationKind



import attrs
from uuid import UUID

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAlbumsInfo:
    # Maps asset UUID to AssetResponseWrapper
    _mapping: Dict[UUID, AssetResponseWrapper]

    def all_album_names(self) -> set[str]:
        """Return a set with all album names found among duplicates."""
        return {album for wrapper in self._mapping.values() for album in wrapper.get_album_names()}

    def get_details(self) -> Dict[UUID, AssetResponseWrapper]:
        """Return the full mapping (read-only)."""
        return dict(self._mapping)

@typechecked
def get_album_from_duplicates(asset_wrapper: "AssetResponseWrapper") -> DuplicateAlbumsInfo:
    """
    For a given asset, if it is a duplicate, returns a DuplicateAlbumsInfo object encapsulating the mapping from each duplicate AssetResponseWrapper (excluding itself)
    to the list of album names it belongs to. This allows for richer traceability and future extensibility.
    If there are no duplicates, returns an empty mapping.
    """
    result: Dict[UUID, AssetResponseWrapper] = {}
    duplicate_wrappers = asset_wrapper.get_duplicate_wrappers()
    for dup_wrapper in duplicate_wrappers:
        result[dup_wrapper.id_as_uuid] = dup_wrapper
    return DuplicateAlbumsInfo(result)


import attrs

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumDecision:
    """
    Encapsulates the decision logic for album assignment, including all album info from duplicates (as DuplicateAlbumsInfo)
    and the album detected from folder structure (if any).
    """
    duplicates_info: DuplicateAlbumsInfo
    album_from_folder: str | None

    def __attrs_post_init__(self):
        # Place breakpoint here for debugging construction
        pass

    def all_options(self) -> set[str]:
        opts = set(self.duplicates_info.all_album_names())
        if self.album_from_folder:
            opts.add(self.album_from_folder)
        return opts

    def valid_albums(self) -> set[str]:
        import re
        return {a for a in self.all_options() if re.match(ALBUM_PATTERN, a)}

    def is_unique(self) -> bool:
        valid = self.valid_albums()
        return len(valid) == 1

    def has_conflict(self) -> bool:
        valid = self.valid_albums()
        return len(valid) > 1

    def get_unique(self) -> str | None:
        valid = self.valid_albums()
        if len(valid) == 1:
            return next(iter(valid))
        return None

    def get_album_origin(self, album: str) -> str:
        if self.album_from_folder == album:
            return "from folders"
        elif album in self.duplicates_info.all_album_names():
            return "from duplicates"
        else:
            return "unknown"

    def __str__(self):
        return f"AlbumDecision(valid={self.valid_albums()}, folder={self.album_from_folder})"


@typechecked
def decide_album_for_asset(asset_wrapper: "AssetResponseWrapper") -> AlbumDecision:
    """
    Returns an AlbumDecision object with all relevant information to decide the album.
    """
    albums_info = get_album_from_duplicates(asset_wrapper)
    detected_album = asset_wrapper.try_detect_album_from_folders()
    return AlbumDecision(duplicates_info=albums_info, album_from_folder=detected_album)


@typechecked
@typechecked
def analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    suppress_album_already_belongs_log: bool = True,
) -> None:
    """
    Handles all logic related to analyzing potential albums for an asset, deciding assignment, and handling conflicts.
    """
    album_decision = decide_album_for_asset(asset_wrapper)
    if album_decision.is_unique():
        detected_album = album_decision.get_unique()
        if detected_album:
            album_origin = album_decision.get_album_origin(detected_album)
            _process_album_detection(asset_wrapper, tag_mod_report, detected_album, album_origin, suppress_album_already_belongs_log=suppress_album_already_belongs_log)
        else:
            print(f"[ALBUM ASSIGNMENT] No valid album found for asset '{asset_wrapper.original_file_name}'. No assignment performed.")
    elif album_decision.has_conflict():
        from immich_autotag.utils.helpers import get_immich_photo_url
        asset_id = asset_wrapper.id_as_uuid
        immich_url = get_immich_photo_url(asset_id)
        albums_info = album_decision.duplicates_info
        print(f"[ALBUM ASSIGNMENT] Asset {asset_wrapper.original_file_name} not assigned to any album due to conflict: multiple valid album options {album_decision.valid_albums()}\nSee asset: {immich_url}")
        details = []
        for _, dup_wrapper in albums_info.get_details().items():
            albums = dup_wrapper.get_album_names()
            details.append(
                f"{dup_wrapper.get_link().geturl()} | file: {dup_wrapper.asset.original_file_name} | date: {dup_wrapper.asset.created_at} | albums: {albums or '[unavailable]'}"
            )
        if details:
            print(f"[ALBUM ASSIGNMENT] Duplicates of {asset_id}:\n" + "\n".join(details))
            raise NotImplementedError(
                f"Ambiguous album assignment for asset {asset_id}: multiple valid albums {album_decision.valid_albums()}\nSee asset: {immich_url}\nDuplicates: {', '.join(details) if details else '-'}"
            )
        # No assignment performed due to ambiguity/conflict
        return


@typechecked
def analyze_duplicate_classification_tags(asset_wrapper: "AssetResponseWrapper") -> None:
    """
    If the asset has duplicates, checks the classification tags of each duplicate.
    If the classification tags (from config) do not match, raises an exception.
    """
    context = asset_wrapper.context
    duplicate_id = asset_wrapper.asset.duplicate_id
    if not duplicate_id:
        return
    wrappers = context.duplicates_collection.get_duplicate_asset_wrappers(asset_wrapper.duplicate_id_as_uuid, context.asset_manager, context)
    for dup_asset_wrapper in wrappers:
        if dup_asset_wrapper.asset.id == asset_wrapper.asset.id:
            continue
        if dup_asset_wrapper is None:
            raise RuntimeError(f"Duplicate asset wrapper not found for asset {dup_asset_wrapper.asset.id}. This should not happen.")
        # Compare tags using a method on AssetResponseWrapper
        if not asset_wrapper.has_same_classification_tags_as(dup_asset_wrapper):
            # Try to auto-fix: if one has a classification tag and the other does not, add it to the one missing it
            tags1 = set(asset_wrapper.get_classification_tags())
            tags2 = set(dup_asset_wrapper.get_classification_tags())
            diff1 = tags1 - tags2
            diff2 = tags2 - tags1
            # Only one asset has classification tags, the other has none
            if tags1 and not tags2 and len(tags1) == 1:
                # Add the tag to dup_asset_wrapper
                tag_to_add = next(iter(tags1))
                print(f"[AUTO-FIX] Adding missing classification tag '{tag_to_add}' to asset {dup_asset_wrapper.asset.id}")
                dup_asset_wrapper.add_tag_by_name(tag_to_add, verbose=True)
                continue
            elif tags2 and not tags1 and len(tags2) == 1:
                # Add the tag to asset_wrapper
                tag_to_add = next(iter(tags2))
                print(f"[AUTO-FIX] Adding missing classification tag '{tag_to_add}' to asset {asset_wrapper.asset.id}")
                asset_wrapper.add_tag_by_name(tag_to_add, verbose=True)
                continue
            # Otherwise, print and raise as before
            link1 = asset_wrapper.get_link().geturl()
            link2 = dup_asset_wrapper.get_link().geturl()
            msg = (
                f"[ERROR] Classification tags differ for duplicates:\n"
                f"Asset 1: {asset_wrapper.asset.id} | {link1}\nTags: {list(tags1)}\n"
                f"Asset 2: {dup_asset_wrapper.asset.id} | {link2}\nTags: {list(tags2)}"
            )
            print(msg)
            raise NotImplementedError(msg)


@typechecked

def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    lock: Lock,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)
    
    analyze_duplicate_classification_tags(asset_wrapper)
    analyze_and_assign_album(asset_wrapper, tag_mod_report, suppress_album_already_belongs_log)

    # If there is no valid album, none is assigned

    validate_and_update_asset_classification(
        asset_wrapper,
        tag_mod_report=tag_mod_report,
    )
    with lock:
        tag_mod_report.flush()

@typechecked
def _process_album_detection(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    detected_album: str,
    album_origin: str,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    # Only log candidate album if not suppressing already-belongs log (i.e., in dry-run/check mode)
    if not suppress_album_already_belongs_log:
        print(
            f"[ALBUM CHECK] Asset '{asset_wrapper.original_file_name}' candidate album: '{detected_album}' (origin: {album_origin})"
        )
    from immich_client.api.albums import add_assets_to_album
    from immich_client.models.albums_add_assets_dto import AlbumsAddAssetsDto

    client = asset_wrapper.context.client
    albums_collection = asset_wrapper.context.albums_collection
    album_wrapper = albums_collection.create_or_get_album_with_user(
        detected_album, client, tag_mod_report=tag_mod_report
    )
    album = album_wrapper.album
    if asset_wrapper.id not in [a.id for a in album.assets or []]:
        print(
            f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' assigned to album '{detected_album}' (origin: {album_origin})"
        )
        try:
            result = add_assets_to_album.sync(
                id=album.id,
                client=client,
                body=BulkIdsDto(ids=[asset_wrapper.id]),
            )
        except Exception as e:
            print(f"[ERROR] Exception when adding asset to album: {e}")
            raise
        # Validación estricta del resultado
        if not isinstance(result, list):
            print(f"[ERROR] Unexpected return type from add_assets_to_album: {type(result)}")
            raise RuntimeError("add_assets_to_album did not return a list")
        found = False
        for item in result:
            try:
                _id = item.id
                _success = item.success
            except AttributeError:
                raise RuntimeError(f"Item in add_assets_to_album response missing required attributes: {item}")
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    error_msg = None
                    try:
                        error_msg = item.error
                    except AttributeError:
                        pass
                    from immich_autotag.utils.helpers import get_immich_photo_url
                    from immich_autotag.utils.get_immich_album_url import get_immich_album_url
                    asset_url = get_immich_photo_url(asset_wrapper.id_as_uuid)
                    album_url = get_immich_album_url(album.id)
                    print(f"[ERROR] Asset {asset_wrapper.id} was not successfully added to album {album.id}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}")
                    print(f"[DEBUG] Full add_assets_to_album response: {result}")
                    raise RuntimeError(
                        f"Asset {asset_wrapper.id} was not successfully added to album {album.id}. "
                        f"Error: {error_msg}. Full response: {result}\n"
                        f"Asset link: {asset_url}\nAlbum link: {album_url}"
                    )
        if not found:
            print(f"[ERROR] Asset {asset_wrapper.id} not found in add_assets_to_album response for album {album.id}")
            print(f"[DEBUG] Full add_assets_to_album response: {result}")
            raise RuntimeError(
                f"Asset {asset_wrapper.id} not found in add_assets_to_album response for album {album.id}. "
                f"Full response: {result}"
            )
        from uuid import UUID
        tag_mod_report.add_assignment_modification(
            kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            asset_id=asset_wrapper.id_as_uuid,
            asset_name=asset_wrapper.original_file_name,
            album_id=UUID(album.id),
            album_name=detected_album,
        )
    else:
        if not suppress_album_already_belongs_log:
            print(
                f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' already in album '{detected_album}' (origin: {album_origin}), no action taken."
            )
