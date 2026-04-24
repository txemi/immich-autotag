# --- AlbumDtoState: encapsulates DTO, load source, and loaded_at timestamp ---
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from urllib.parse import ParseResult
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.types import Unset
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_cache_entry import AlbumCacheEntry

from immich_autotag.albums.album.album_dto_state import AlbumLoadSource
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AlbumUUID, UserUUID

if TYPE_CHECKING:
    from immich_autotag.types.uuid_wrappers import AssetUUID
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.report.modification_entry import ModificationEntry
    from immich_autotag.context.immich_context import ImmichContext

from immich_autotag.albums.albums.album_error_history import AlbumErrorHistory
from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.albums.album.album_user_list import AlbumUserList
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_kind import ModificationKind


@attrs.define(auto_attribs=True, slots=True)
class AlbumPartialRepr:
    album_name: str | None
    partial_repr: str


class AssetAlreadyInAlbumError(Exception):
    """
    Raised when trying to add an asset to an album and it is already present.
    This is not a fatal error for most workflows.
    """

    pass


@attrs.define(auto_attribs=True, slots=True)
class AlbumResponseWrapper:

    # (No manual __slots__ definition; rely on attrs fields only)

    # --- 1. Fields ---
    _cache_entry: AlbumCacheEntry = attrs.field()
    _deleted_at: datetime.datetime | None = attrs.field(default=None, init=False)
    _unavailable: bool = attrs.field(default=False, init=False)
    _error_history: AlbumErrorHistory = attrs.field(
        factory=AlbumErrorHistory,
        init=False,
        repr=False,
    )

    # --- 2. Special Methods ---
    def __attrs_post_init__(self) -> None:
        pass

    def get_start_date(self) -> datetime.datetime | Unset:
        """
        Returns the album's start date as a datetime object, or None if not available.
        """
        return self._cache_entry.get_start_date()

    def get_end_date(self) -> datetime.datetime | Unset:
        """
        Returns the album's end date as a datetime object, or None if not available.
        """
        return self._cache_entry.get_end_date()

    def get_start_date_cached(self) -> datetime.datetime | Unset:
        """
        Returns start date from current cached DTO without forcing a full reload.
        """
        return self._cache_entry.get_start_date_cached()

    def get_end_date_cached(self) -> datetime.datetime | Unset:
        """
        Returns end date from current cached DTO without forcing a full reload.
        """
        return self._cache_entry.get_end_date_cached()

    @typechecked
    def get_asset_count(self) -> int:
        """
        Returns album asset count from DTO metadata without forcing a full reload.
        """
        return self._cache_entry.get_asset_count()

    # --- 3. Properties ---
    @property
    @typechecked
    def owner_uuid(self) -> UserUUID:
        """Returns the AlbumUUID of the album owner."""
        # Return the UserUUID wrapper as expected by the type annotation
        return self._cache_entry.get_owner_uuid()

    # --- 4. Static Methods ---
    @staticmethod
    @typechecked
    def get_default_client() -> ImmichClient:
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

        return ImmichClientWrapper.get_default_instance().get_client()

    # --- 5. Public Methods - Metadata and Identification ---

    @typechecked
    def get_album_uuid(self) -> AlbumUUID:
        return self._cache_entry.get_album_id()

    @typechecked
    def get_album_name(self) -> str:
        return self._cache_entry.get_album_name()

    @conditional_typechecked
    def get_immich_album_url(self) -> "ParseResult":
        from immich_autotag.utils.url_helpers import get_immich_album_url

        return get_immich_album_url(self.get_album_uuid())

    @typechecked
    def is_temporary_album(self) -> bool:
        """
        Returns True if this album is a temporary autotag album
        (created automatically by autotag).
        """
        from immich_autotag.assets.albums.temporary_manager.naming import (
            is_temporary_album,
        )

        return is_temporary_album(self.get_album_name())

    @typechecked
    def is_duplicate_album(self) -> bool:
        """
        Returns True if this album is a duplicate album (i.e., there is more than one
        album with the same name in the collection).
        """
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )

        collection = AlbumCollectionWrapper.get_instance()
        return collection.is_duplicated(self)

    @typechecked
    def get_album_users(self) -> "AlbumUserList":
        """
        Returns an AlbumUserList encapsulating all users in the album (album_users).
        This provides a robust, consistent interface for album user access.
        """
        return self._cache_entry.get_album_users()

    @typechecked
    def get_owner_uuid(self) -> "UserUUID":
        """Returns the UUID of the album owner (UUID object, not string)."""
        # Return the raw UUID as expected by the type annotation
        owner_uuid = self._cache_entry.get_owner_uuid()
        return owner_uuid

    # --- 6. Public Methods - Asset Management ---

    @conditional_typechecked
    def get_asset_uuids(self) -> set["AssetUUID"]:
        """
        Returns the asset IDs as a set of AssetUUID objects using the AlbumCacheEntry logic.
        """
        return self._cache_entry.get_asset_uuids()

    @conditional_typechecked
    def get_asset_ids(self) -> set["AssetUUID"]:
        """
        Returns the set of asset IDs as AssetUUIDs using the AlbumCacheEntry logic.
        """
        return self._cache_entry.get_asset_uuids()

    @conditional_typechecked
    def has_asset(self, asset: "AssetResponseDto") -> bool:
        from immich_autotag.types.uuid_wrappers import AssetUUID

        return (
            AssetUUID.from_uuid(UUID(asset.id)) in self._cache_entry.get_asset_uuids()
        )

    @conditional_typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        return self._cache_entry.has_asset_wrapper(asset_wrapper)

    @conditional_typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        # Ensure the album is fully loaded before accessing assets
        return self._cache_entry.get_assets(context)

    @typechecked
    def is_empty(self) -> bool:
        """
        Returns True if the album has no assets, False otherwise.
        Optimized: does not force reload or cache construction if not needed.
        """
        return self._cache_entry.is_empty()

    # --- Moved: _update_from_dto and _set_album_full are now in AlbumCacheEntry ---

    # --- 10. Private Methods - Error Handling and Verification ---

    # --- 7. Public Methods - Lifecycle and State ---
    @conditional_typechecked
    @typechecked
    def merge_from_dto(
        self, dto: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> None:
        """
        Delegates to AlbumCacheEntry.merge_from_dto. See AlbumCacheEntry for logic.
        """
        self._cache_entry.merge_from_dto(dto, load_source)

    def _is_full(self) -> bool:
        return self._cache_entry.is_full()

    @typechecked
    def has_loaded_assets(self) -> bool:
        return self._is_full()

    @typechecked
    def is_deleted(self) -> bool:
        """
        Returns True if the album has been logically deleted (i.e., _deleted_at is set).
        """
        return self._deleted_at is not None

    @typechecked
    def _mark_deleted(self) -> None:
        """
        Logically mark this album as deleted by setting _deleted_at to now.
        """
        if self._deleted_at is None:
            self._deleted_at = datetime.datetime.now()

    @typechecked
    def mark_deleted(self) -> None:
        """
        Public method to logically mark this album as deleted.
        """
        self._mark_deleted()

    @typechecked
    def should_mark_unavailable(
        self, threshold: int | None = None, window_seconds: int | None = None
    ) -> bool:
        try:
            from immich_autotag.config.internal_config import ALBUM_ERROR_THRESHOLD

            th = int(threshold) if threshold is not None else int(ALBUM_ERROR_THRESHOLD)
            return self._error_history.count_in_window(window_seconds) >= th
        except Exception:
            return False

    @typechecked
    def _validate_before_add(self, asset_wrapper: "AssetResponseWrapper") -> None:
        """Validates if an asset can be added to the album."""
        if self.has_asset_wrapper(asset_wrapper):
            raise AssetAlreadyInAlbumError(
                f"Asset {asset_wrapper.get_id()} is already in album {self.get_album_uuid()}"
            )

    # --- 8. Public Methods - Modification Actions ---
    @conditional_typechecked
    def add_asset(
        self,
        *,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        modification_report: "ModificationReport",
        raise_on_duplicate: bool = True,
    ) -> "ModificationEntry | None":
        """
        Adds an asset to the album. If the asset is already present and raise_on_duplicate=True,
        raises AssetAlreadyInAlbumError. If raise_on_duplicate=False, logs warning and returns None.

        Args:
            raise_on_duplicate: If True, raises AssetAlreadyInAlbumError when asset is already in album.
                               If False, logs warning and continues execution.

        Returns:
            ModificationEntry if successful or None if asset already in album and raise_on_duplicate=False.
        """
        # 1. Validation
        self._validate_before_add(asset_wrapper)

        # 2. Execution
        entry: ModificationEntry | None = self._cache_entry._execute_add_asset_api(
            asset_wrapper=asset_wrapper,
            client=client,
            album_wrapper=self,
            raise_on_duplicate=raise_on_duplicate,
        )

        # If entry is None, asset was already in album and we're not raising
        if entry is not None and entry.kind is ModificationKind.ASSIGN_ASSET_TO_ALBUM:
            pass
        elif (
            entry is not None
            and entry.kind is ModificationKind.WARNING_ASSET_ALREADY_IN_ALBUM
        ):
            pass
        else:
            raise NotImplementedError(
                "Unexpected case: entry is None but kind is ASSIGN_ASSET_TO_ALBUM, or entry is not None but kind is not ASSIGN_ASSET_TO_ALBUM"
            )

        # Update the asset-to-albums mapping in the collection to avoid duplicates in get_or_create
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )

        AlbumCollectionWrapper.get_instance().update_asset_to_albums_map_for_asset(
            asset=asset_wrapper, album=self
        )
        return entry

    @typechecked
    def _ensure_removal_allowed(self) -> None:
        """Enforces safety rules for asset removal."""
        if not (self.is_temporary_album() or self.is_duplicate_album()):
            raise RuntimeError(
                f"Refusing to remove asset from album '{self.get_album_name()}' "
                f"(id={self.get_album_uuid()}): not a temporary or duplicate album."
            )

    @conditional_typechecked
    def remove_asset(
        self,
        *,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        modification_report: "ModificationReport",
    ) -> ModificationEntry | None:
        """
        Removes the asset from the album using the API and validates the result.

        Safe to call even if asset is not in album (idempotent operation).
        Raises exception only if the removal fails unexpectedly.

        Updates the album collection's asset-to-albums mapping to keep cache in sync.
        """
        # 1. Validation
        self._ensure_removal_allowed()
        report_mod_entry = self._cache_entry.remove_asset(
            asset_wrapper=asset_wrapper, album=self
        )

        # 2. Update album collection cache to reflect the removal
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )

        AlbumCollectionWrapper.get_instance().remove_asset_from_album_in_map(
            asset=asset_wrapper, album=self
        )

        return report_mod_entry

    @conditional_typechecked
    def remove_asset_for_conversion(
        self,
        *,
        asset_wrapper: "AssetResponseWrapper",
    ) -> ModificationEntry | None:
        """
        Removes the asset from this album as part of a MOVE conversion.
        Unlike remove_asset(), not restricted to temporary or duplicate albums.
        """
        report_mod_entry = self._cache_entry.remove_asset(
            asset_wrapper=asset_wrapper, album=self
        )
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )
        AlbumCollectionWrapper.get_instance().remove_asset_from_album_in_map(
            asset=asset_wrapper, album=self
        )
        return report_mod_entry

    @conditional_typechecked
    def trim_name_if_needed(
        self,
        *,
        client: ImmichClient,
        modification_report: "ModificationReport",
    ) -> None:
        album_name = self.get_album_name()
        if album_name.startswith(" "):
            cleaned_name = album_name.strip()

            from immich_client.models.update_album_dto import UpdateAlbumDto

            from immich_autotag.api.immich_proxy.albums.update_album_info import (
                proxy_update_album_info,
            )

            update_body = UpdateAlbumDto(album_name=cleaned_name)
            proxy_update_album_info(
                album_id=self.get_album_uuid(),
                client=client,
                body=update_body,
            )
            from immich_autotag.report.modification_kind import ModificationKind

            modification_report.add_album_modification(
                kind=ModificationKind.RENAME_ALBUM,
                album=self,
                old_value=album_name,
                new_value=cleaned_name,
            )
            log(
                f"Album '{album_name}' renamed to '{cleaned_name}'",
                level=LogLevel.FOCUS,
            )

    # Responsibility moved: Album creation/retrieval from DTO now belongs to AlbumCollectionWrapper singleton.

    @typechecked
    def rename_album(
        self,
        *,
        new_name: str,
        client: ImmichClient,
        modification_report: "ModificationReport",
    ) -> "ModificationEntry | None":
        """
        Renames the album using the API and updates the cache entry and modification report.
        Args:
            new_name: The new name to assign to the album.
            client: The ImmichClient instance for API calls.
            modification_report: The ModificationReport for logging changes.
        """
        current_name = self.get_album_name()
        if new_name == current_name:
            raise ValueError(
                f"Attempted to rename album '{self.get_album_uuid()}' to the same name '{new_name}'. Operation is not allowed."
            )

        from immich_client.models.update_album_dto import UpdateAlbumDto

        from immich_autotag.api.immich_proxy.albums.update_album_info import (
            proxy_update_album_info,
        )

        update_body = UpdateAlbumDto(album_name=new_name)
        updated_dto = proxy_update_album_info(
            album_id=self.get_album_uuid(),
            client=client,
            body=update_body,
        )
        # Update cache entry using AlbumDtoState.update

        from immich_autotag.albums.album.album_dto_state import AlbumLoadSource

        self._cache_entry._dto.update(
            dto=updated_dto, load_source=AlbumLoadSource.UPDATE
        )
        report_entry = modification_report.add_album_modification(
            kind=ModificationKind.RENAME_ALBUM,
            album=self,
            old_value=current_name,
            new_value=new_name,
        )
        log(
            f"Album '{self.get_album_uuid()}' renamed to '{new_name}'",
            level=LogLevel.FOCUS,
        )
        return report_entry

    def get_best_cache_entry(
        self, other: "AlbumResponseWrapper"
    ) -> "AlbumResponseWrapper":
        """
        Decide which AlbumResponseWrapper is preferred for merging/updating.
        Delegates to AlbumCacheEntry.get_best_cache_entry.
        """
        best_entry = self._cache_entry.get_best_cache_entry(other._cache_entry)
        return self if best_entry is self._cache_entry else other
