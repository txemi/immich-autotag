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
from immich_autotag.types import ImmichClient

if TYPE_CHECKING:
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.context.immich_context import ImmichContext

from immich_autotag.albums.albums.album_error_history import AlbumErrorHistory
from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.albums.album.album_user_list import AlbumUserList
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log


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

    # --- 1. Fields ---
    _cache_entry: AlbumCacheEntry = attrs.field(kw_only=True)
    _deleted_at: datetime.datetime | None = attrs.field(default=None, init=False)

    _asset_ids_cache: set[str] | None = attrs.field(default=None, init=False)
    _unavailable: bool = attrs.field(default=False, init=False)

    from immich_autotag.albums.albums.album_error_history import AlbumErrorHistory

    _error_history: AlbumErrorHistory = attrs.field(
        factory=AlbumErrorHistory,
        init=False,
        repr=False,
    )

    # --- 2. Special Methods ---
    def __attrs_post_init__(self) -> None:
        pass

    # --- 3. Properties ---
    @property
    @typechecked
    def owner_uuid(self) -> "UUID":
        """Returns the UUID of the album owner (UUID object, not string)."""

        return self._cache_entry.get_state().get_owner_uuid()

    # --- 4. Static Methods ---
    @staticmethod
    @typechecked
    def get_default_client() -> ImmichClient:
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

        return ImmichClientWrapper.get_default_instance().get_client()

    @staticmethod
    @typechecked
    def _find_asset_result_in_response(
        result: list[BulkIdResponseDto], asset_id: UUID
    ) -> BulkIdResponseDto | None:
        """Finds the result item for a specific asset in the API response list."""
        for item in result:
            if item.success is not True:
                raise RuntimeError(
                    "API returned non-boolean success value in BulkIdResponseDto"
                )
            if UUID(item.id) == asset_id:
                return item

        return None

    # --- 5. Public Methods - Metadata and Identification ---

    @typechecked
    def get_album_uuid(self) -> "UUID":
        return self._cache_entry.get_state().get_album_id()

    @typechecked
    def get_album_name(self) -> str:
        return self._cache_entry.get_state().get_album_name()

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

    @conditional_typechecked
    def _ensure_full_album_loaded(self, client: ImmichClient) -> AlbumResponseWrapper:
        if self._cache_entry.get_state().get_load_source() == AlbumLoadSource.DETAIL:
            return self
        self.reload_from_api(client)
        return self

    @typechecked
    def get_album_users(self) -> "AlbumUserList":
        """
        Returns an AlbumUserList encapsulating all users in the album (album_users).
        This provides a robust, consistent interface for album user access.
        """
        return self._cache_entry.get_state().get_album_users()

    @typechecked
    def get_owner_uuid(self) -> "UUID":
        """Returns the UUID of the album owner (UUID object, not string)."""
        return self._cache_entry.get_state().get_owner_uuid()

    def _get_album_full_or_load_dto(self) -> AlbumResponseDto:
        """
        Returns the full AlbumResponseDto, loading it from the API if necessary.
        Ensures the album is in DETAIL/full mode.
        """
        return self.get_uuid()

    @typechecked
    def _get_or_build_asset_ids_cache(self) -> set[UUID]:
        """
        Returns the set of asset IDs as UUIDs, using the AlbumCacheEntry logic.
        """
        return self._cache_entry.get_asset_uuids()

    # --- 6. Public Methods - Asset Management ---

    @conditional_typechecked
    def get_asset_uuids(self) -> set[UUID]:
        """
        Returns the asset IDs as a set of UUID objects using the AlbumCacheEntry logic.
        """
        return self._cache_entry.get_asset_uuids()

    @conditional_typechecked
    def get_asset_ids(self) -> set[UUID]:
        """
        Returns the set of asset IDs as UUIDs using the AlbumCacheEntry logic.
        """
        return self._cache_entry.get_asset_uuids()

    @conditional_typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        from uuid import UUID

        return UUID(asset.id) in self._get_or_build_asset_ids_cache()

    @conditional_typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        from uuid import UUID

        return UUID(asset_wrapper.asset.id) in self._get_or_build_asset_ids_cache()

    @conditional_typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        # Assets are authoritative in the full DTO. Load the full DTO if
        # needed and return wrapped assets. This avoids relying on the
        # partial DTO for asset information.
        assets = self._cache_entry.get_assets()
        return [context.asset_manager.get_wrapper_for_asset(a, context) for a in assets]

    @typechecked
    def is_empty(self) -> bool:
        """
        Returns True if the album has no assets, False otherwise.
        Optimized: does not force reload or cache construction if not needed.
        """
        assets = self._ensure_full_album_loaded(
            self.get_default_client()
        )._cache_entry.is_empty()
        return assets

    def _update_from_dto(
        self, dto: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> None:
        self._cache_entry.get_state().update(dto=dto, load_source=load_source)
        self.invalidate_cache()

    @typechecked
    def _set_album_full(self, value: AlbumResponseDto) -> None:
        self._update_from_dto(value, AlbumLoadSource.DETAIL)

        self.invalidate_cache()

    # --- 10. Private Methods - Error Handling and Verification ---
    @typechecked
    def _build_partial_repr(self) -> AlbumPartialRepr:
        """Builds a safe partial representation of the album for error logs."""
        try:
            album_name: str | None = None
            dto_id: str | None = None
            try:
                album_name = self.get_album_name()
            except Exception:
                album_name = None
            try:
                dto_id = self.get_album_uuid()
            except Exception:
                dto_id = None
            partial_repr = f"AlbumDTO(id={dto_id!r}, name={album_name!r})"
        except Exception:
            album_name = None
            partial_repr = "<unrepresentable album_partial>"
        return AlbumPartialRepr(album_name=album_name, partial_repr=partial_repr)

    def _handle_recoverable_400(
        self, api_exc: AlbumApiExceptionInfo, partial: AlbumPartialRepr
    ) -> None:
        """Handles 400 error (not found/no access) in a recoverable way."""
        self._error_history.append_api_exc(api_exc)
        current_count = self._error_history.count_in_window()
        # Include the album link in the log for diagnostics
        album_url = self.get_immich_album_url().geturl()
        log_msg = (
            f"[WARN] get_album_info returned 400 for album id="
            f"{self.get_album_uuid()!r} name={partial.album_name!r}. "
            f"Recorded recoverable error (count={current_count}). "
            f"album_partial={partial.partial_repr} album_link={album_url}"
        )
        log(
            log_msg,
            level=LogLevel.WARNING,
        )
        from immich_autotag.config.internal_config import (
            ALBUM_ERROR_THRESHOLD,
            ALBUM_ERROR_WINDOW_SECONDS,
        )

        if self.should_mark_unavailable(
            ALBUM_ERROR_THRESHOLD, ALBUM_ERROR_WINDOW_SECONDS
        ):
            self._unavailable = True
            self.invalidate_cache()
            from immich_autotag.report.modification_kind import (
                ModificationKind,
            )
            from immich_autotag.report.modification_report import (
                ModificationReport,
            )

            tag_mod_report = ModificationReport.get_instance()
            extra = {"recent_errors": len(self._error_history), "album": self}
            tag_mod_report.add_error_modification(
                kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
                error_message=partial.partial_repr,
                error_category="HTTP_400",
                extra=extra,
            )
            from immich_autotag.albums.albums.album_collection_wrapper import (
                AlbumCollectionWrapper,
            )

            AlbumCollectionWrapper.get_instance().notify_album_marked_unavailable(self)

    def _log_and_raise_fatal_error(
        self, api_exc: AlbumApiExceptionInfo, partial: AlbumPartialRepr
    ) -> None:
        log(
            (
                f"[FATAL] get_album_info failed for album id={self.get_album_uuid()!r} "
                f"name={partial.album_name!r}. Exception: {api_exc.exc!r}. "
                f"album_partial={partial.partial_repr}"
            ),
            level=LogLevel.ERROR,
        )
        raise api_exc.exc

    # --- 7. Public Methods - Lifecycle and State ---
    @conditional_typechecked
    def reload_from_api(self, client: ImmichClient) -> AlbumResponseWrapper:
        """Reloads the album DTO from the API and clears the cache, delegando el fetch pero gestionando errores y reporting aquí."""
        from immich_client import errors as immich_errors

        from immich_autotag.albums.albums.album_api_exception_info import (
            AlbumApiExceptionInfo,
        )
        album_dto_before = self._cache_entry._dto
        try:
            self._cache_entry.ensure_full_loaded()
        except RuntimeError as exc:
            # Aquí se puede distinguir por mensaje o tipo de error si se quiere lógica más fina
            api_exc = AlbumApiExceptionInfo(exc)
            partial = self._build_partial_repr()
            # Ejemplo: si el error es asimilable a un 400, marcar como unavailable y reportar
            if api_exc.is_status(400):
                self._handle_recoverable_400(api_exc, partial)                return self
            self._log_and_raise_fatal_error(api_exc, partial)
        album_dto_after = self._cache_entry._dto
        if album_dto_after is None:
            raise RuntimeError(
                f"get_album_info.sync returned None for album id="
                f"{self.get_album_uuid_no_cache()}"
            )
        if album_dto_after is not album_dto_before:
            self.invalidate_cache()
        return self

    @typechecked
    def merge_from_dto(
        self, dto: AlbumResponseDto, load_source: AlbumLoadSource
    ) -> None:
        """
        Unifies DTO update logic. Updates the wrapper with the new DTO and load_source if:
                - The new load_source is DETAIL (always update to full)
                - The current load_source is SEARCH (allow update from SEARCH to SEARCH or
                    DETAIL)
        - Ensures loaded_at is monotonic (never decreases)
        - Updates asset ID cache as UUIDs
        If the current is DETAIL and the new is SEARCH, ignores the update.
        """
        should_update = False
        if load_source == AlbumLoadSource.DETAIL:
            should_update = True
        elif self._load_source == AlbumLoadSource.SEARCH:
            should_update = True
        if should_update:
            self._update_from_dto(dto, load_source)

    def _is_full(self) -> bool:
        return self._cache_entry.get_state().is_full()

    @typechecked
    def ensure_full(self) -> AlbumResponseWrapper:
        if self._unavailable:
            raise RuntimeError(
                "Album is marked unavailable; cannot ensure full DTO for this album"
            )
        if not self._is_full():
            self.reload_from_api(self.get_default_client())
        return self

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
    def invalidate_cache(self) -> None:
        self._asset_ids_cache = None

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
            album_id=self.get_album_uuid_no_cache(),
            client=client,
            asset_ids=[asset_wrapper.get_id_as_uuid()],
        )
        if not isinstance(result, list):
            raise RuntimeError(
                f"add_assets_to_album did not return a list, got {type(result)}"
            )
        return result

    @typechecked
    def _report_addition_to_modification_report(
        self,
        asset_wrapper: "AssetResponseWrapper",
        tag_mod_report: "ModificationReport",
    ) -> None:
        """Records the asset addition in the modification report."""
        from immich_autotag.report.modification_kind import ModificationKind

        tag_mod_report.add_assignment_modification(
            kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            asset_wrapper=asset_wrapper,
            album=self,
        )

    def _handle_add_asset_error(
        self,
        item: object,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        """Handles non-success results from addition API."""
        try:
            error_msg = item.error
        except AttributeError:
            error_msg = None

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
            self.reload_from_api(client)

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
            self.reload_from_api(client)
            if self.has_asset_wrapper(asset_wrapper):
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
    ) -> None:
        """
        Adds an asset to the album. If the asset is already present,
        raises AssetAlreadyInAlbumError.
        """
        # 1. Validation
        self._validate_before_add(asset_wrapper)

        # 2. Execution
        result = self._execute_add_asset_api(asset_wrapper, client)

        # 3. Handle result
        item = self._find_asset_result_in_response(
            result, asset_wrapper.get_id_as_uuid()
        )
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
        self._report_addition_to_modification_report(asset_wrapper, tag_mod_report)

        # 5. Consistency Verification
        self._verify_asset_in_album_with_retry(asset_wrapper, client, max_retries=3)

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
            album_id=self.get_album_uuid_no_cache(),
            client=client,
            asset_ids=[asset_wrapper.get_id_as_uuid()],
        )
        if not isinstance(result, list):
            raise RuntimeError(
                f"remove_assets_from_album did not return a list, got {type(result)}"
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
        from immich_autotag.config._internal_types import ErrorHandlingMode
        from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE

        if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
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
        self, item: object, asset_wrapper: "AssetResponseWrapper"
    ) -> None:
        """Handles non-success results from removal API."""
        from immich_autotag.config._internal_types import ErrorHandlingMode
        from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE

        try:
            error_msg = item.error
        except AttributeError:
            error_msg = None

        asset_url = asset_wrapper.get_immich_photo_url().geturl()
        album_url = self.get_immich_album_url().geturl()

        # Handle known recoverable errors
        if error_msg and (str(error_msg).lower() in ("not_found", "no_permission")):
            if str(error_msg).lower() == "not_found":
                self._handle_album_not_found_during_removal(
                    error_msg, asset_url, album_url
                )
                return

            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise RuntimeError(
                    (
                        f"Asset {asset_wrapper.get_id()} was not successfully removed from "
                        f"album {self.get_album_uuid()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    )
                )
            else:
                log(
                    (
                        f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} could not be removed from "
                        f"album {self.get_album_uuid()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    ),
                    level=LogLevel.WARNING,
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
            self.reload_from_api(client)
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
                self._handle_remove_asset_error(item, asset_wrapper)
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
        raise NotImplementedError("from_partial_dto has been removed.")
        state = AlbumDtoState.create(dto=dto, load_source=AlbumLoadSource.SEARCH)
        cache_entry = AlbumCacheEntry(dto=state)
        return cls(cache_entry=cache_entry)

    def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial
        """Equality based on album id when possible."""
        if not isinstance(other, AlbumResponseWrapper):
            return False
        try:
            return self.get_album_uuid() == other.get_album_uuid()
        except Exception:
            return False

    def __hash__(self) -> int:  # pragma: no cover - trivial
        """Hash by album id when available; fallback to object id.

        This allows storing wrappers in sets while reasoning by identity via
        the album id (which is stable and unique per album).
        """
        try:
            return hash(self.get_album_uuid())
        except Exception:
            return object.__hash__(self)

    # Eliminado: toda recarga de álbum debe pasar por AlbumCacheEntry.ensure_full_loaded
