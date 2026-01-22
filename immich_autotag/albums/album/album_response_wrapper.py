from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import ParseResult
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.types import ImmichClient

if TYPE_CHECKING:
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.context.immich_context import ImmichContext

from immich_autotag.albums.albums.album_api_exception_info import AlbumApiExceptionInfo
from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

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




import datetime
import enum


class AlbumLoadSource(enum.Enum):
    SEARCH = "search"  # Loaded from album list/search API
    DETAIL = "detail"  # Loaded from album detail API (full)

@attrs.define(auto_attribs=True, slots=True)
class AlbumResponseWrapper:

    # Either `_album_partial` or `_album_full` will be present depending on
    # how the wrapper was constructed. Allow `_album_partial` to be None so
    # callers can create an instance explicitly from a full DTO.

    _album_dto: AlbumResponseDto = attrs.field(kw_only=True)
    _asset_ids_cache: set[str] | None = attrs.field(default=None, init=False)
    _unavailable: bool = attrs.field(default=False, init=False)
    _loaded_at: datetime.datetime = attrs.field(factory=datetime.datetime.now, init=False)
    _deleted_at: datetime.datetime | None = attrs.field(default=None, init=False)
    _load_source: AlbumLoadSource = attrs.field(default=AlbumLoadSource.SEARCH, init=True)
    from immich_autotag.albums.albums.album_error_history import AlbumErrorHistory
    _error_history: AlbumErrorHistory = attrs.field(
        factory=AlbumErrorHistory,
        init=False,
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """
        Ensure the wrapper has a DTO and set _loaded_at to now if not already set.
        """
        if self._album_dto is None:
            raise ValueError("AlbumResponseWrapper must be constructed with a DTO.")
        if not hasattr(self, "_loaded_at") or self._loaded_at is None:
            self._loaded_at = datetime.datetime.now()

    @typechecked
    def _update_dto(self, new_dto: AlbumResponseDto, source: AlbumLoadSource) -> None:
        """
        Update the internal DTO with a new one, updating the load source and loaded_at.
        loaded_at must always increase.
        """
        now = datetime.datetime.now()
        if now < self._loaded_at:
            raise RuntimeError("New loaded_at timestamp is earlier than previous loaded_at.")
        self._album_dto = new_dto
        self._load_source = source
        self._loaded_at = now

    @typechecked
    def _mark_deleted(self) -> None:
        """
        Logically mark this album as deleted by setting _deleted_at to now.
        """
        if self._deleted_at is None:
            self._deleted_at = datetime.datetime.now()


    @typechecked
    def is_deleted(self) -> bool:
        """
        Returns True if the album has been logically deleted (i.e., _deleted_at is set).
        """
        return self._deleted_at is not None

    @typechecked
    def mark_deleted(self) -> None:
        """
        Public method to logically mark this album as deleted.
        """
        self._mark_deleted()
    @property
    @typechecked
    def owner_uuid(self) -> "UUID":
        """Returns the UUID of the album owner (UUID object, not string)."""
        from uuid import UUID
        return UUID(self._album_dto.owner_id)

    @typechecked
    def is_temporary_album(self) -> bool:
        """
        Returns True if this album is a temporary autotag album (created automatically by autotag).
        """
        from immich_autotag.assets.albums.temporary_manager.naming import (
            is_temporary_album,
        )

        return is_temporary_album(self.get_album_name())

    def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial
        """Equality based on album id when possible."""
        if not isinstance(other, AlbumResponseWrapper):
            return False
        try:
            return self.get_album_id() == other.get_album_id()
        except Exception:
            return False

    def __hash__(self) -> int:  # pragma: no cover - trivial
        """Hash by album id when available; fallback to object id.

        This allows storing wrappers in sets while reasoning by identity via
        the album id (which is stable and unique per album).
        """
        try:
            return hash(self.get_album_id())
        except Exception:
            return object.__hash__(self)
    @conditional_typechecked
    def get_asset_uuids(self) -> set[UUID]:
        """
        Returns the asset IDs as a set of UUID objects.
        """
        from uuid import UUID
        return set(UUID(asset_id) for asset_id in self.get_asset_ids())


    @typechecked
    def is_empty(self) -> bool:
        """
        Returns True if the album has no assets, False otherwise.
        Uses the cached asset ids if available for efficiency.
        """
        return len(self.get_asset_ids()) == 0

    @typechecked
    def is_duplicate_album(self) -> bool:
        """
        Returns True if this album is a duplicate album (i.e., there is more than one album with the same name in the collection).
        Si el álbum no se encuentra entre los duplicados, hace un resync y vuelve a comprobar antes de lanzar excepción.
        """
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )
        from immich_autotag.context.immich_context import ImmichContext

        collection = AlbumCollectionWrapper.get_instance()
        album_name = self.get_album_name()
        same_name_albums = list(collection.find_all_albums_with_name(album_name))
        album_ids = [a.get_album_id() for a in same_name_albums]
        if self.get_album_id() not in album_ids:
            if True:
                aaa = list(collection.find_all_albums_with_name(album_name))
                raise RuntimeError(
                    f"Album with id={self.get_album_id()} and name='{self.get_album_name()}' not found among albums with the same name: {album_ids}"
                )
            else:
                # Intentar resync de la colección y volver a comprobar
                client = ImmichContext.get_default_client()
                new_collection = AlbumCollectionWrapper.resync_from_api(client)
                same_name_albums = list(
                    new_collection.find_all_albums_with_name(album_name)
                )
                album_ids = [a.get_album_id() for a in same_name_albums]
                if self.get_album_id() not in album_ids:
                    raise RuntimeError(
                        f"Album with id={self.get_album_id()} and name='{album_name}' not found among albums with the same name (tras resync): {album_ids}"
                    )
        return len(same_name_albums) > 1

    @staticmethod
    @typechecked
    def get_default_client() -> ImmichClient:
        from immich_autotag.context.immich_context import ImmichContext

        return ImmichContext.get_default_client()

    @property
    def is_full(self) -> bool:
        # Defensive: assets should be a list[AssetResponseDto], but check type to avoid always-true condition
        if self._album_full is None:
            return False
        assets = getattr(self._album_full, "assets", None)
        if not isinstance(assets, list):
            return False
        # Defensive: assets should be a list[AssetResponseDto], but type checkers may not know
        return len(assets) > 0

    @typechecked

    def get_album_id(self) -> str:
        return self._album_dto.id

    @typechecked

    def get_album_name(self) -> str:
        return self._album_dto.album_name

    @typechecked

    def get_album_uuid(self) -> "UUID":
        from uuid import UUID
        return UUID(self.get_album_id())

    @typechecked
    def get_album_uuid_no_cache(self) -> "UUID":
        """Return the album UUID without using any cache (always computed).

        This method intentionally avoids relying on any cached value and
        computes the UUID from the current album id on each call.
        """
        return UUID(self.get_album_id())

    @typechecked
    def ensure_full(self) -> None:
        # If the album has been explicitly marked unavailable, fail fast so
        # callers become aware and can handle the condition. Do not silently
        # continue as that hides real problems.
        if self._unavailable:
            raise RuntimeError(
                "Album is marked unavailable; cannot ensure full DTO for this album"
            )

        if not self.is_full:
            self.reload_from_api(self.get_default_client())

    @typechecked
    def _get_partial(self) -> AlbumResponseDto:
        assert self._album_partial is not None
        return self._album_partial

    @typechecked
    def _get_full(self) -> AlbumResponseDto:
        return self._get_album_full_or_load()

    @typechecked
    def _active_dto(self) -> AlbumResponseDto:
        """Return the DTO currently held by the wrapper (partial or full).

        Raises ValueError if neither representation is present. Use this
        helper to avoid repeating `self._album_partial or self._album_full`.
        """
        dto = self._album_partial or self._album_full
        if dto is None:
            raise ValueError("AlbumResponseWrapper has no DTO (partial or full)")
        return dto

    @typechecked
    def _set_album_full(self, value: AlbumResponseDto) -> None:
        self._album_full = value

    @typechecked
    def invalidate_cache(self) -> None:
        try:
            self._asset_ids_cache = None
        except Exception:
            pass

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

    @conditional_typechecked
    def reload_from_api(self, client: ImmichClient) -> None:
        """Reloads the album DTO from the API and clears the cache."""
        from immich_client import errors as immich_errors

        from immich_autotag.albums.album.album_api_utils import get_album_info_by_id
        from immich_autotag.albums.albums.album_api_exception_info import (
            AlbumApiExceptionInfo,
        )

        album_dto = None
        try:
            album_dto = get_album_info_by_id(self.get_album_uuid_no_cache(), client)
        except immich_errors.UnexpectedStatus as exc:
            api_exc = AlbumApiExceptionInfo(exc)
            partial = self._build_partial_repr()
            if api_exc.is_status(400):
                self._handle_recoverable_400(api_exc, partial)
                return
            self._log_and_raise_fatal_error(api_exc, partial)
        if album_dto is None:
            raise RuntimeError(
                f"get_album_info.sync returned None for album id={self.get_album_uuid_no_cache()}"
            )
        else:
            self._set_album_full(album_dto)
            self.invalidate_cache()

    @typechecked
    def _build_partial_repr(self) -> AlbumPartialRepr:
        """Construye una representación parcial segura del álbum para logs de error."""
        try:
            album_name: str | None = None
            dto_id: str | None = None
            asset_count: int | None = None
            try:
                album_name = self.get_album_name()
            except Exception:
                album_name = None
            try:
                dto_id = self.get_album_id()
            except Exception:
                dto_id = None
            try:
                # Use get_asset_ids() for asset count if possible
                asset_count = len(self.get_asset_ids())
            except Exception:
                asset_count = None
            partial_repr = (
                f"AlbumDTO(id={dto_id!r}, name={album_name!r}, assets={asset_count})"
            )
        except Exception:
            album_name = None
            partial_repr = "<unrepresentable album_partial>"
        return AlbumPartialRepr(album_name=album_name, partial_repr=partial_repr)

    # _extract_status_code_from_exc is now handled by AlbumApiExceptionInfo

    def _handle_recoverable_400(
        self, api_exc: AlbumApiExceptionInfo, partial: AlbumPartialRepr
    ) -> None:
        """Gestiona el error 400 (no encontrado/sin acceso) de forma recuperable."""
        self._error_history.append_api_exc(api_exc)
        current_count = self._error_history.count_in_window()
        log(
            (
                f"[WARN] get_album_info returned 400 for album id="
                f"{self.get_album_id()!r} name={partial.album_name!r}. "
                f"Recorded recoverable error (count={current_count}). "
                f"album_partial={partial.partial_repr}"
            ),
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
            from immich_autotag.report.modification_report import (
                ModificationReport,
            )
            from immich_autotag.report.modification_kind import (
                ModificationKind,
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
                f"[FATAL] get_album_info failed for album id={self.get_album_id()!r} "
                f"name={partial.album_name!r}. Exception: {api_exc.exc!r}. "
                f"album_partial={partial.partial_repr}"
            ),
            level=LogLevel.ERROR,
        )
        raise api_exc.exc

    @conditional_typechecked
    def _ensure_full_album_loaded(self, client: ImmichClient) -> None:
        if self._album_full is not None:
            return
        self.reload_from_api(client)

    @conditional_typechecked
    def _get_album_full_or_load(self) -> AlbumResponseDto:
        from immich_autotag.context.immich_context import ImmichContext

        client = ImmichContext.get_default_client()
        self._ensure_full_album_loaded(client)
        if self._album_full is None:

            self._ensure_full_album_loaded(client)
            raise RuntimeError()
        return self._album_full

    def get_asset_ids(self) -> set[str]:
        if self._asset_ids_cache is not None:
            return self._asset_ids_cache

        # Ensure album full data is loaded (may raise)
        self.ensure_full()
        assets = self._get_album_full_or_load().assets or []
        self._asset_ids_cache = set(a.id for a in assets)
        return self._asset_ids_cache

    @conditional_typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        return asset.id in self.get_asset_ids()

    @conditional_typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        if use_cache:
            return asset_wrapper.asset.id in self.get_asset_ids()
        else:
            return self.has_asset(asset_wrapper.asset)

    @conditional_typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        # Assets are authoritative in the full DTO. Load the full DTO if
        # needed and return wrapped assets. This avoids relying on the
        # partial DTO for asset information.
        assets = self._get_album_full_or_load().assets or []
        return [context.asset_manager.get_wrapper_for_asset(a, context) for a in assets]

    from typing import Optional

    @conditional_typechecked
    def trim_name_if_needed(
        self,
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        album_name = self.get_album_name()
        if album_name.startswith(" "):
            cleaned_name = album_name.strip()
            from immich_client.api.albums import update_album_info
            from immich_client.models.update_album_dto import UpdateAlbumDto

            update_body = UpdateAlbumDto(album_name=cleaned_name)
            from uuid import UUID

            update_album_info.sync(
                id=UUID(self.get_album_id()),
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

    @conditional_typechecked
    def get_immich_album_url(self) -> "ParseResult":
        from urllib.parse import urlparse

        from immich_autotag.config.host_config import get_immich_web_base_url

        url = f"{get_immich_web_base_url()}/albums/{self.get_album_id()}"
        return urlparse(url)

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
        from immich_client.api.albums import add_assets_to_album
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        # Avoid adding if already present (explicit, clear)
        if self.has_asset_wrapper(asset_wrapper):
            raise AssetAlreadyInAlbumError(
                f"Asset {asset_wrapper.id} is already in album {self.get_album_id()}"
            )

        result = add_assets_to_album.sync(
            id=self.get_album_uuid_no_cache(),
            client=client,
            body=BulkIdsDto(ids=[asset_wrapper.id_as_uuid]),
        )

        # Strict validation of the result
        if not isinstance(result, list):
            raise RuntimeError(
                f"add_assets_to_album did not return a list, got {type(result)}"
            )

        item = self._find_asset_result_in_response(result, str(asset_wrapper.id))
        if item:
            if not item.success:
                self._handle_add_asset_error(
                    item, asset_wrapper, client, tag_mod_report
                )
        else:
            raise RuntimeError(
                (
                    f"Asset {asset_wrapper.id} not found in add_assets_to_album response for album "
                    f"{self.get_album_id()}."
                )
            )

        from immich_autotag.report.modification_kind import ModificationKind

        tag_mod_report.add_assignment_modification(
            kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            asset_wrapper=asset_wrapper,
            album=self,
        )
        # If requested, invalidate cache after operation and validate with retry logic
        self._verify_asset_in_album_with_retry(asset_wrapper, client, max_retries=3)

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
                    f"Asset {asset_wrapper.id} already in album "
                    f"{self.get_album_id()} (API duplicate error). "
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
                        f"Asset {asset_wrapper.id} was not successfully added to album {self.get_album_id()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    ),
                },
            )
            from immich_autotag.albums.album.album_response_wrapper import (
                AssetAlreadyInAlbumError,
            )

            raise AssetAlreadyInAlbumError(
                f"Asset {asset_wrapper.id} already in album {self.get_album_id()} (API duplicate error)"
            )
        else:
            raise RuntimeError(
                (
                    f"Asset {asset_wrapper.id} was not successfully added to album "
                    f"{self.get_album_id()}: {error_msg}\n"
                    f"Asset link: {asset_url}\n"
                    f"Album link: {album_url}"
                )
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
        from immich_client.api.albums import remove_asset_from_album
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        # Enforce safety: only allow removal from temporary or duplicate albums
        self._ensure_removal_allowed()

        # Check if asset is in album first (use has_asset_wrapper for clarity)
        if not self.has_asset_wrapper(asset_wrapper):
            log(
                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} is not in album {self.get_album_id()}, "
                "skipping removal.",
                level=LogLevel.DEBUG,
            )
            return

        # Remove asset from album
        result = remove_asset_from_album.sync(
            id=self.get_album_uuid_no_cache(),
            client=client,
            body=BulkIdsDto(ids=[asset_wrapper.id_as_uuid]),
        )

        # Validate the result
        if not isinstance(result, list):
            raise RuntimeError(
                f"remove_assets_from_album did not return a list, got {type(result)}"
            )

        item = self._find_asset_result_in_response(result, str(asset_wrapper.id))
        if item:
            if not item.success:
                self._handle_remove_asset_error(item, asset_wrapper)
        else:
            # Not found in response
            log(
                (
                    f"[ALBUM REMOVAL] Asset {asset_wrapper.id} not found in remove_assets_from_album "
                    f"response for album {self.get_album_id()}. Treating as already removed."
                ),
                level=LogLevel.WARNING,
            )
            from immich_autotag.config._internal_types import ErrorHandlingMode
            from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE

            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise RuntimeError(
                    (
                        f"Asset {asset_wrapper.id} not found in remove_assets_from_album response for album "
                        f"{self.get_album_id()}."
                    )
                )
            return

        # Log successful removal
        log(
            (
                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} removed from album {self.get_album_id()} "
                f"('{self.get_album_name()}')."
            ),
            level=LogLevel.FOCUS,
        )

        # Track modification if report provided
        if tag_mod_report:
            from immich_autotag.report.modification_kind import ModificationKind

            tag_mod_report.add_assignment_modification(
                kind=ModificationKind.REMOVE_ASSET_FROM_ALBUM,
                asset_wrapper=asset_wrapper,
                album=self,
            )

        # Invalidate cache and verify removal with retry logic
        self._verify_asset_removed_from_album_with_retry(
            asset_wrapper, client, max_retries=3
        )

    @typechecked
    def _ensure_removal_allowed(self) -> None:
        """Enforces safety rules for asset removal."""
        if not (self.is_temporary_album() or self.is_duplicate_album()):
            raise RuntimeError(
                f"Refusing to remove asset from album '{self.get_album_name()}' "
                f"(id={self.get_album_id()}): not a temporary or duplicate album."
            )

    @staticmethod
    @typechecked
    def _find_asset_result_in_response(
        result: list[BulkIdResponseDto], asset_id: str
    ) -> object | None:
        """Finds the result item for a specific asset in the API response list."""
        for item in result:
            try:
                if item.id == asset_id:
                    # Enforce existence of success attribute
                    _ = item.success
                    return item
            except AttributeError:
                raise RuntimeError(
                    f"Item in API response missing required attributes (id/success): {item}"
                )
        return None

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
                        f"Asset {asset_wrapper.id} was not successfully removed from album "
                        f"{self.get_album_id()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    )
                )
            else:
                log(
                    (
                        f"[ALBUM REMOVAL] Asset {asset_wrapper.id} could not be removed from album "
                        f"{self.get_album_id()}: {error_msg}\n"
                        f"Asset link: {asset_url}\n"
                        f"Album link: {album_url}"
                    ),
                    level=LogLevel.WARNING,
                )
                return

        # Otherwise, treat as fatal
        raise RuntimeError(
            (
                f"Asset {asset_wrapper.id} was not successfully removed from album "
                f"{self.get_album_id()}: {error_msg}\n"
                f"Asset link: {asset_url}\n"
                f"Album link: {album_url}"
            )
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
                    f"[ALBUM REMOVAL] Album {self.get_album_id()} "
                    f"('{self.get_album_name()}') removed from collection due to "
                    f"not_found error during asset removal."
                ),
                level=LogLevel.FOCUS,
            )
        except Exception as e:
            log(
                (
                    f"[ALBUM REMOVAL] Failed to remove album {self.get_album_id()} "
                    f"from collection after not_found: {e}"
                ),
                level=LogLevel.WARNING,
            )

        log(
            (
                f"[ALBUM REMOVAL] Asset could not be removed because album {self.get_album_id()} "
                f"was not found (HTTP 404): {error_msg}\n"
                f"Asset link: {asset_url}\n"
                f"Album link: {album_url}"
            ),
            level=LogLevel.WARNING,
        )

    @conditional_typechecked
    def _verify_asset_in_album_with_retry(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        max_retries: int = 3,
    ) -> None:
        """
        Verifies that an asset appears in the album after adding it, with retry logic for eventual consistency.
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
                        f"After {max_retries} retries, asset {asset_wrapper.id} does NOT appear in album "
                        f"{self.get_album_id()}. This may be an eventual consistency or API issue."
                    ),
                    level=LogLevel.WARNING,
                )

    @conditional_typechecked
    def _verify_asset_removed_from_album_with_retry(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        max_retries: int = 3,
    ) -> None:
        """
        Verifies that an asset has been removed from the album after removing it, with retry logic for eventual consistency.
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
                        f"After {max_retries} retries, asset {asset_wrapper.id} still appears in album "
                        f"{self.get_album_id()}. This may be an eventual consistency or API issue."
                    ),
                    level=LogLevel.WARNING,
                )

    @staticmethod
    @conditional_typechecked
    def from_id(
        client: ImmichClient,
        album_id: UUID,
        tag_mod_report: ModificationReport,
    ) -> "AlbumResponseWrapper":
        """
        Gets an album by ID, wraps it, and trims the name if necessary.
        """

        from immich_autotag.albums.albums.album_api_utils import get_album_info_by_id

        album_full = get_album_info_by_id(album_id, client)
        if album_full is None:
            raise RuntimeError(f"get_album_info returned no album for id={album_id}")
        wrapper = AlbumResponseWrapper.from_full_dto(
            album_full, validate=False, tag_mod_report=tag_mod_report
        )
        wrapper.trim_name_if_needed(client=client, tag_mod_report=tag_mod_report)
        return wrapper

    @staticmethod
    @conditional_typechecked
    def from_partial_dto(
        dto: AlbumResponseDto,
    ) -> "AlbumResponseWrapper":
        """
        Create an AlbumResponseWrapper from a partial DTO.

        The wrapper will store the provided DTO as _album_partial and will not populate the full cache.
        Callers must explicitly request loading the full DTO via ensure_full/reload_from_api.
        """
        # Create instance with required _album_dto argument
        wrapper = AlbumResponseWrapper(album_dto=dto, load_source=AlbumLoadSource.SEARCH)

        return wrapper

    @staticmethod
    @conditional_typechecked
    def from_full_dto(
        dto: AlbumResponseDto,
        *,
        validate: bool = True,
        tag_mod_report: ModificationReport | None = None,
    ) -> "AlbumResponseWrapper":
        """
        Create an AlbumResponseWrapper from a full DTO.

        This constructor treats the provided DTO as the authoritative full
        representation: `_album_full` will be set and `_album_partial` will
        be left as None to make it explicit what representation the wrapper
        holds. If `validate` is True, a basic sanity check is performed to
        ensure the DTO contains `assets` before accepting it as full.
        """
        if validate:
            try:
                assets_check = dto.assets
            except AttributeError:
                assets_check = None
            if assets_check is None:
                raise ValueError(
                    "Provided DTO does not contain assets; cannot treat as full DTO"
                )

        # Construct instance without calling __init__ / attrs post-init so we
        # can set the full DTO explicitly. This avoids triggering the
        # `__attrs_post_init__` check which expects a valid representation
        # during normal construction paths.
        wrapper = object.__new__(AlbumResponseWrapper)
        # Set the expected attributes directly for a full representation.
        wrapper._album_partial = None
        wrapper._album_full = dto
        wrapper._asset_ids_cache = None
        try:
            assets = dto.assets or []
            wrapper._asset_ids_cache = set(a.id for a in assets)
        except Exception:
            wrapper._asset_ids_cache = None

        return wrapper

    @typechecked
    def get_album_users(self) -> "AlbumUserList":
        """
        Returns an AlbumUserList encapsulating all users in the album (album_users).
        This provides a robust, consistent interface for album user access.
        """
        from immich_autotag.albums.album.album_user_list import AlbumUserList
        from immich_autotag.albums.album.album_user_wrapper import AlbumUserWrapper

        dto = self._active_dto()
        users = [AlbumUserWrapper(user=u) for u in dto.album_users]
        return AlbumUserList(users)
