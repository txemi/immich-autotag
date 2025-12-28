from __future__ import annotations
from typing import Set

from threading import Lock

from immich_client.models.bulk_ids_dto import BulkIdsDto
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.tags.tag_modification_report import TagModificationReport

from immich_autotag.assets.asset_validation import validate_and_update_asset_classification
from immich_autotag.config.user import TAG_CONVERSIONS, ALBUM_PATTERN
from immich_autotag.tags.modification_kind import ModificationKind

@typechecked
def get_album_from_duplicates(asset_wrapper: "AssetResponseWrapper") -> Set[str]:
    """
    If the asset is a duplicate, checks if any of its duplicates already has an album and returns the set of all found albums.
    If there are no duplicates with albums, returns an empty set.
    """
    from uuid import UUID
    context = asset_wrapper.context
    duplicate_id = asset_wrapper.asset.duplicate_id
    albums_for_duplicates = set()
    if duplicate_id is not None:
        group = context.duplicates_collection.get_group(UUID(duplicate_id))
        albums_collection = context.albums_collection
        for dup_id in group:
            # Skip the asset itself
            if str(dup_id) == asset_wrapper.asset.id:
                continue
            dup_asset = context.asset_manager.get_asset(dup_id, context)
            if dup_asset is not None:
                albums = albums_collection.albums_for_asset(dup_asset.asset)
                albums_for_duplicates.update(albums)
    return albums_for_duplicates


import attrs
@attrs.define(auto_attribs=True, slots=True, frozen=True)

class AlbumDecision:
    albums_from_duplicates: set[str]
    album_from_folder: str | None

    def all_options(self) -> set[str]:
        opts = set(self.albums_from_duplicates)
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
        elif album in self.albums_from_duplicates:
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
    import re
    albums_from_duplicates = get_album_from_duplicates(asset_wrapper)
    # Filtrar solo los que cumplen el patrón
    filtered_duplicates = {a for a in albums_from_duplicates if re.match(ALBUM_PATTERN, a)}
    detected_album = asset_wrapper.try_detect_album_from_folders()
    return AlbumDecision(albums_from_duplicates=filtered_duplicates, album_from_folder=detected_album)


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
        context = asset_wrapper.context
        duplicate_id = asset_wrapper.duplicate_id_as_uuid
        duplicate_links = context.duplicates_collection.get_duplicate_asset_links(duplicate_id)
        print(f"[ALBUM ASSIGNMENT] Asset {asset_wrapper.original_file_name} not assigned to any album due to conflict: multiple valid album options {album_decision.valid_albums()}\nSee asset: {immich_url}")
        if duplicate_links:
            # Use the new API to get AssetResponseWrapper objects for all duplicates
            wrappers = context.duplicates_collection.get_duplicate_asset_wrappers(duplicate_id, context.asset_manager, context)
            details = [
                f"{w.get_link().geturl()} | albums: {w.get_album_names() or '[unavailable]'}"
                for w in wrappers
            ]
            print(f"[ALBUM ASSIGNMENT] Duplicates of {asset_id}:\n" + "\n".join(details))
            # This situation requires user intervention: ambiguous album assignment due to duplicates.
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
    group = context.duplicates_collection.get_group(asset_wrapper.duplicate_id_as_uuid)
    for dup_id in group:
        if str(dup_id) == asset_wrapper.asset.id:
            continue
        dup_asset_wrapper = context.asset_manager.get_asset(dup_id, context)
        if dup_asset_wrapper is None:
            raise RuntimeError(f"Duplicate asset wrapper not found for asset {dup_id}. This should not happen.")
        # Compare tags using a method on AssetResponseWrapper
        if not asset_wrapper.has_same_classification_tags_as(dup_asset_wrapper):
            raise NotImplementedError(
                f"Classification tags differ for duplicates: {asset_wrapper.asset.id} vs {dup_id}"
            )


@typechecked

def process_single_asset(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "TagModificationReport",
    lock: Lock,
    suppress_album_already_belongs_log: bool = True,
) -> None:
    asset_wrapper.apply_tag_conversions(TAG_CONVERSIONS, tag_mod_report=tag_mod_report)
    
    analyze_and_assign_album(asset_wrapper, tag_mod_report, suppress_album_already_belongs_log)
    analyze_duplicate_classification_tags(asset_wrapper)

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
            # Comprobación estricta de atributos sin hasattr ni getattr
            try:
                _id = item.id
                _success = item.success
            except AttributeError:
                raise RuntimeError(f"Item in add_assets_to_album response missing required attributes: {item}")
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    # El atributo error puede no estar siempre, pero si está lo mostramos
                    error_msg = None
                    try:
                        error_msg = item.error
                    except AttributeError:
                        pass
                    print(f"[ERROR] Asset {asset_wrapper.id} was not successfully added to album {album.id}: {error_msg}")
                    raise RuntimeError(f"Asset {asset_wrapper.id} was not successfully added to album {album.id}")
        if not found:
            print(f"[ERROR] Asset {asset_wrapper.id} not found in add_assets_to_album response for album {album.id}")
            raise RuntimeError(f"Asset {asset_wrapper.id} not found in add_assets_to_album response")
        tag_mod_report.add_assignment_modification(
            kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            asset_id=asset_wrapper.id,
            asset_name=asset_wrapper.original_file_name,
            album_id=album.id,
            album_name=detected_album,
        )
    else:
        if not suppress_album_already_belongs_log:
            print(
                f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.original_file_name}' already in album '{detected_album}' (origin: {album_origin}), no action taken."
            )
