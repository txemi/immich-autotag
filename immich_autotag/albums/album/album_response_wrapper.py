# --- AlbumDtoState: encapsulates DTO, load source, and loaded_at timestamp ---
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING
from urllib.parse import ParseResult
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from typeguard import typechecked

from immich_autotag.albums.album.album_cache_entry import AlbumCacheEntry
from immich_autotag.albums.album.album_dto_state import AlbumDtoState, AlbumLoadSource
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AlbumUUID, UserUUID

if TYPE_CHECKING:
    from immich_autotag.types.uuid_wrappers import AssetUUID

if TYPE_CHECKING:
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

    def get_start_date(self) -> datetime.datetime | None:
        """
        Returns the album's start date as a datetime object, or None if not available.
        """
        return self._cache_entry.get_start_date()

    def get_end_date(self) -> datetime.datetime | None:
        """
        Returns the album's end date as a datetime object, or None if not available.
        """
        return self._cache_entry.get_end_date()

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

    @staticmethod
    @typechecked
    def _find_asset_result_in_response(
        result: list[BulkIdResponseDto], asset_id: "AssetUUID"
    ) -> BulkIdResponseDto | None:
        """Finds the result item for a specific asset in the API response list."""
        from immich_autotag.types.uuid_wrappers import AssetUUID

        for item in result:
            # Validate that success is a boolean (can be True or False)
            if not isinstance(item.success, bool):
                raise RuntimeError(
                    f"API returned non-boolean success value in BulkIdResponseDto: {type(item.success)} = {item.success}"
                )
            if AssetUUID.from_uuid(UUID(item.id)) == asset_id:
                return item

        return None

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

    @typechecked
    def _execute_add_asset_api(
        self, asset_wrapper: "AssetResponseWrapper", client: ImmichClient
    ) -> list[BulkIdResponseDto]:
        """Executes the API call to add an asset to the album."""
        from immich_autotag.api.immich_proxy.albums import proxy_add_assets_to_album

        result = proxy_add_assets_to_album(
            album_id=self.get_album_uuid(),
            client=client,
            asset_ids=[asset_wrapper.get_id()],
        )
        return result

    @typechecked
    def _report_addition_to_modification_report(
        self,
        asset_wrapper: "AssetResponseWrapper",
        tag_mod_report: "ModificationReport",
    ) -> "ModificationEntry":
        """Records the asset addition in the modification report."""
        from immich_autotag.report.modification_kind import ModificationKind

        return tag_mod_report.add_assignment_modification(
            kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            asset_wrapper=asset_wrapper,
            album=self,
        )

    def _handle_add_asset_error(
        self,
        item: BulkIdResponseDto,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        """Handles non-success results from addition API."""
        error_msg = item.error
        asset_url = asset_wrapper.get_immich_photo_url().geturl()
        album_url = self.get_immich_album_url().geturl()

        # If the error is 'duplicate', reactive refresh:
        # reload album data from API.
        if error_msg and "duplicate" in str(error_msg).lower():
            log(
                (
                    f"Asset {asset_wrapper.get_id()} already in album "
                    f"{self.get_album_uuid()} (API duplicate error). "
                    f"Raising AssetAlreadyInAlbumError."
                ),
                level=LogLevel.FOCUS,
            )
            # Instead of self.reload_from_api, use _cache_entry.ensure_full_loaded if available
            # AlbumCacheEntry._ensure_full_loaded is protected; use get_asset_uuids to force reload
            self._cache_entry.get_asset_uuids()

            from immich_autotag.report.modification_kind import ModificationKind

            tag_mod_report.add_assignment_modification(
                kind=ModificationKind.WARNING_ASSET_ALREADY_IN_ALBUM,
                asset_wrapper=asset_wrapper,
                album=self,
                extra={
                    "error": error_msg,
                    "asset_url": asset_url,
                    "album_url": album_url,
                    "reason": "Stale cached album data detected and reloaded",
                    "details": (
                        f"Asset {asset_wrapper.get_id()} was not successfully added to album "
                        f"{self.get_album_uuid()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    ),
                },
            )
            from immich_autotag.albums.album.album_response_wrapper import (
                AssetAlreadyInAlbumError,
            )

            raise AssetAlreadyInAlbumError(
                f"Asset {asset_wrapper.get_id()} already in album "
                f"{self.get_album_uuid()} (API duplicate error)"
            )
        else:
            raise RuntimeError(
                (
                    f"Asset {asset_wrapper.get_id()} was not successfully added to album "
                    f"{self.get_album_uuid()}: {error_msg}\n"
                    f"Asset link: {asset_url}\n"
                    f"Album link: {album_url}"
                )
            )

    @conditional_typechecked
    def _verify_asset_in_album_with_retry(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        max_retries: int = 3,
    ) -> None:
        """
        Verifies that an asset appears in the album after adding it,
        with retry logic for eventual consistency.
        Uses exponential backoff to handle API delays.
        """
        import time

        for attempt in range(max_retries):
            if self._cache_entry.has_asset_wrapper(asset_wrapper):
                return  # Success - asset is in album

            if attempt < max_retries - 1:
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                wait_time = 0.1 * (2**attempt)
                time.sleep(wait_time)
            else:
                log(
                    (
                        f"After {max_retries} retries, asset {asset_wrapper.get_id()} "
                        f"does NOT appear in album {self.get_album_uuid()}. "
                        f"This may be an eventual consistency or "
                        f"API issue."
                    ),
                    level=LogLevel.WARNING,
                )

    # --- 8. Public Methods - Modification Actions ---
    @conditional_typechecked
    def add_asset(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> "ModificationEntry":
        """
        Adds an asset to the album. If the asset is already present,
        raises AssetAlreadyInAlbumError.
        Returns the ModificationEntry created by the operation.
        """
        # 1. Validation
        self._validate_before_add(asset_wrapper)

        # 2. Execution
        result = self._execute_add_asset_api(asset_wrapper, client)

        # 3. Handle result
        item = self._find_asset_result_in_response(result, asset_wrapper.get_id())
        if item:
            if not item.success:
                self._handle_add_asset_error(
                    item, asset_wrapper, client, tag_mod_report
                )
        else:
            raise RuntimeError(
                f"Asset {asset_wrapper.get_id()} not found in add_assets_to_album response."
            )

        # 4. Reporting
        entry = self._report_addition_to_modification_report(
            asset_wrapper, tag_mod_report
        )

        # 5. Consistency Verification
        self._verify_asset_in_album_with_retry(asset_wrapper, client, max_retries=3)

        return entry

    @typechecked
    def _ensure_removal_allowed(self) -> None:
        """Enforces safety rules for asset removal."""
        if not (self.is_temporary_album() or self.is_duplicate_album()):
            raise RuntimeError(
                f"Refusing to remove asset from album '{self.get_album_name()}' "
                f"(id={self.get_album_uuid()}): not a temporary or duplicate album."
            )

    @typechecked
    def _validate_before_remove(self, asset_wrapper: "AssetResponseWrapper") -> bool:
        """Validates if an asset removal is allowed and necessary."""
        self._ensure_removal_allowed()

        if not self.has_asset_wrapper(asset_wrapper):
            log(
                f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} is not in album "
                f"{self.get_album_uuid()}, skipping removal.",
                level=LogLevel.DEBUG,
            )
            return False
        return True

    @typechecked
    def _execute_remove_asset_api(
        self, asset_wrapper: "AssetResponseWrapper", client: ImmichClient
    ) -> list[BulkIdResponseDto]:
        """Executes the API call to remove an asset from the album."""
        from immich_autotag.api.immich_proxy.albums import proxy_remove_asset_from_album

        result = proxy_remove_asset_from_album(
            album_id=self.get_album_uuid(),
            client=client,
            asset_ids=[asset_wrapper.get_id()],
        )
        return result

    @typechecked
    def _handle_missing_remove_response(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> None:
        """Handles the case where the asset is not found in the removal response."""
        log(
            (
                f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} not found in "
                f"remove_assets_from_album response for album "
                f"{self.get_album_uuid()}. Treating as already removed."
            ),
            level=LogLevel.WARNING,
        )
        from immich_autotag.config.dev_mode import is_development_mode

        if is_development_mode():
            raise RuntimeError(
                f"Asset {asset_wrapper.get_id()} not found in removal response for album "
                f"{self.get_album_uuid()}."
            )

    @typechecked
    def _report_removal_to_modification_report(
        self,
        asset_wrapper: "AssetResponseWrapper",
        tag_mod_report: "ModificationReport",
    ) -> None:
        """Records the asset removal in the modification report."""
        if tag_mod_report:
            from immich_autotag.report.modification_kind import ModificationKind

            tag_mod_report.add_assignment_modification(
                kind=ModificationKind.REMOVE_ASSET_FROM_ALBUM,
                asset_wrapper=asset_wrapper,
                album=self,
            )

    def _handle_album_not_found_during_removal(
        self, error_msg: str | None, asset_url: str, album_url: str
    ) -> None:
        """Handles the case where the album is missing during an asset removal."""
        try:
            from immich_autotag.albums.albums.album_collection_wrapper import (
                AlbumCollectionWrapper,
            )

            collection = AlbumCollectionWrapper.get_instance()
            collection.remove_album_local(self)
            log(
                (
                    f"[ALBUM REMOVAL] Album {self.get_album_uuid()} "
                    f"('{self.get_album_name()}') removed from collection due to "
                    f"not_found error during asset removal."
                ),
                level=LogLevel.FOCUS,
            )
        except Exception as e:
            log(
                (
                    f"[ALBUM REMOVAL] Failed to remove album {self.get_album_uuid()} "
                    f"from collection after not_found: {e}"
                ),
                level=LogLevel.WARNING,
            )

        log(
            (
                f"[ALBUM REMOVAL] Asset could not be removed because album "
                f"{self.get_album_uuid()} was not found (HTTP 404): {error_msg}\n"
                f"Asset link: {asset_url}\n"
                f"Album link: {album_url}"
            ),
            level=LogLevel.WARNING,
        )

    def _handle_remove_asset_error(
        self,
        item: BulkIdResponseDto,
        asset_wrapper: "AssetResponseWrapper",
        tag_mod_report: "ModificationReport",
    ) -> None:
        """Handles non-success results from removal API."""
        from immich_client.types import UNSET

        error_msg: str | None = None if item.error is UNSET else str(item.error)
        asset_url = asset_wrapper.get_immich_photo_url().geturl()
        album_url = self.get_immich_album_url().geturl()

        # Handle known recoverable errors
        if error_msg is not None and (
            str(error_msg).lower() in ("not_found", "no_permission")
        ):
            if str(error_msg).lower() == "not_found":
                self._handle_album_not_found_during_removal(
                    error_msg, asset_url, album_url
                )
                # Asset not found in album - likely due to stale cache data
                # This is not a fatal error, just log as warning and continue
                log(
                    (
                        f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} could not be removed from "
                        f"album {self.get_album_uuid()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    ),
                    level=LogLevel.WARNING,
                )
                # Register warning event in modification report
                tag_mod_report.add_assignment_modification(
                    kind=ModificationKind.WARNING_ASSET_NOT_IN_ALBUM,
                    asset_wrapper=asset_wrapper,
                    album=self,
                    extra={"error": error_msg},
                )
                return

        # Otherwise, treat as fatal
        raise RuntimeError(
            (
                f"Asset {asset_wrapper.get_id()} was not successfully removed from album "
                f"{self.get_album_uuid()}: {error_msg}\n"
                f"Asset link: {asset_url}\n"
                f"Album link: {album_url}"
            )
        )

    @conditional_typechecked
    def _verify_asset_removed_from_album_with_retry(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        max_retries: int = 3,
    ) -> None:
        """
        Verifies that an asset has been removed from the album after removing it,
        with retry logic for eventual consistency.
        Uses exponential backoff to handle API delays.
        """
        import time

        for attempt in range(max_retries):
            if not self.has_asset_wrapper(asset_wrapper):
                return  # Success - asset is no longer in album

            if attempt < max_retries - 1:
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                wait_time = 0.1 * (2**attempt)
                time.sleep(wait_time)
            else:
                log(
                    (
                        f"After {max_retries} retries, asset {asset_wrapper.get_id()} "
                        f"still appears in album {self.get_album_uuid()}. "
                        f"This may be an eventual consistency or API issue."
                    ),
                    level=LogLevel.WARNING,
                )

    @conditional_typechecked
    def remove_asset(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        """
        Removes the asset from the album using the API and validates the result.

        Safe to call even if asset is not in album (idempotent operation).
        Raises exception only if the removal fails unexpectedly.
        """
        # 1. Validation
        if not self._validate_before_remove(asset_wrapper):
            return

        # 2. Execution
        result = self._execute_remove_asset_api(asset_wrapper, client)

        # 3. Handle result
        item = self._find_asset_result_in_response(result, asset_wrapper.get_id())
        if item:
            if not item.success:
                self._handle_remove_asset_error(item, asset_wrapper, tag_mod_report)
        else:
            self._handle_missing_remove_response(asset_wrapper)
            return

        # 4. Success Log
        log(
            (
                f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} removed from album "
                f"{self.get_album_uuid()} ('{self.get_album_name()}')."
            ),
            level=LogLevel.FOCUS,
        )

        # 5. Reporting
        self._report_removal_to_modification_report(asset_wrapper, tag_mod_report)

        # 6. Consistency Verification
        self._verify_asset_removed_from_album_with_retry(
            asset_wrapper, client, max_retries=3
        )

    @conditional_typechecked
    def trim_name_if_needed(
        self,
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        album_name = self.get_album_name()
        if album_name.startswith(" "):
            cleaned_name = album_name.strip()

            from immich_client.models.update_album_dto import UpdateAlbumDto

            from immich_autotag.api.immich_proxy.albums import proxy_update_album_info

            update_body = UpdateAlbumDto(album_name=cleaned_name)
            proxy_update_album_info(
                album_id=self.get_album_uuid(),
                client=client,
                body=update_body,
            )
            from immich_autotag.report.modification_kind import ModificationKind

            tag_mod_report.add_album_modification(
                kind=ModificationKind.RENAME_ALBUM,
                album=self,
                old_value=album_name,
                new_value=cleaned_name,
            )
            log(
                f"Album '{album_name}' renamed to '{cleaned_name}'",
                level=LogLevel.FOCUS,
            )

    @classmethod
    @typechecked
    def from_partial_dto(cls, dto: AlbumResponseDto) -> "AlbumResponseWrapper":
        from immich_autotag.albums.album.album_cache_entry import AlbumCacheEntry

        state = AlbumDtoState.create(dto=dto, load_source=AlbumLoadSource.SEARCH)
        cache_entry = AlbumCacheEntry.create(dto=state)
        # See docs/dev/style/python_static_factory_pattern.md for why we use this pattern:
        # attrs with kw_only fields and validators are incompatible with direct kwarg construction in some cases.
        # So we use a no-argument constructor and assign the field directly.
        # See: docs/dev/style/python_static_factory_pattern.md#attrs-single-argument-constructor-pattern

        obj = cls(cache_entry)  # Now positional
        return obj

    def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial
        """Equality based on album id when possible.

        If 'other' is not an AlbumResponseWrapper, raise TypeError to signal improper comparison usage.
        """
        if not isinstance(other, AlbumResponseWrapper):
            raise TypeError(
                f"Cannot compare AlbumResponseWrapper with {type(other).__name__}"
            )
        return self.get_album_uuid() == other.get_album_uuid()

    def __hash__(self) -> int:  # pragma: no cover - trivial
        """Hash by album id when available; fallback to object id.

        This allows storing wrappers in sets while reasoning by identity via
        the album id (which is stable and unique per album).
        """
        try:
            return hash(self.get_album_uuid())
        except Exception:
            return object.__hash__(self)
