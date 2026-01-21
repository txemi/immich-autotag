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

from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.albums.albums.album_error_entry import AlbumErrorEntry
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log


class AssetAlreadyInAlbumError(Exception):
    """
    Raised when trying to add an asset to an album and it is already present.
    This is not a fatal error for most workflows.
    """

    pass


@attrs.define(auto_attribs=True, slots=True)
class AlbumResponseWrapper:



    # Either `_album_partial` or `_album_full` will be present depending on
    # how the wrapper was constructed. Allow `_album_partial` to be None so
    # callers can create an instance explicitly from a full DTO.
    _album_partial: AlbumResponseDto | None = attrs.field(default=None)
    _album_full: AlbumResponseDto | None = attrs.field(default=None, init=False)
    # Explicit cache for asset ids. Use get_asset_ids() to access.
    _asset_ids_cache: set[str] | None = attrs.field(default=None, init=False)
    # If True, the album is known to be unavailable (deleted or no access).
    # When unavailable we avoid API reload attempts and treat asset list as empty.
    _unavailable: bool = attrs.field(default=False, init=False)
    # Recent error history for this album: list of AlbumErrorEntry objects
    _error_history: list[AlbumErrorEntry] = attrs.field(
        default=attrs.Factory(list), init=False, repr=False
    )

    def __attrs_post_init__(self) -> None:
        """
        Ensure the wrapper reflects a concrete representation: at least one of
        `_album_partial` or `_album_full` must be present after construction.
        """
        if self._album_partial is None and self._album_full is None:
            raise ValueError(
                (
                    "AlbumResponseWrapper must be constructed with either a partial or "
                    "full DTO"
                )
            )
    @property
    @typechecked
    def owner_uuid(self) -> "UUID":
        """Devuelve el UUID del owner del álbum (objeto UUID, no string)."""
        from uuid import UUID
        # El owner_id puede estar en _album_partial o _album_full
        album = self._album_full or self._album_partial
        if album is None or not hasattr(album, "owner_id"):
            raise AttributeError("AlbumResponseWrapper: owner_id not available.")
        return UUID(album.owner_id)


        
    @typechecked
    def is_temporary_album(self) -> bool:
        """
        Returns True if this album is a temporary autotag album (created automatically by autotag).
        """
        from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album
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
        This uses the AlbumCollectionWrapper singleton to ensure consistent duplicate detection.
        Raises if the current album is not found among the albums with the same name (should never happen in normal operation).
        """
        from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
        collection = AlbumCollectionWrapper.get_instance()
        same_name_albums = list(collection.albums_with_name(self.get_album_name()))
        album_ids = [a.get_album_id() for a in same_name_albums]
        if self.get_album_id() not in album_ids:
            raise RuntimeError(
                f"Album with id={self.get_album_id()} and name='{self.get_album_name()}' not found among albums with the same name: {album_ids}"
            )
        return len(same_name_albums) > 1
    @staticmethod
    @typechecked
    def get_default_client() -> ImmichClient:
        from immich_autotag.context.immich_context import ImmichContext

        return ImmichContext.get_default_client()

    @property
    def is_full(self) -> bool:
        return self._album_full is not None and self._album_full.assets is not None

    @typechecked
    def get_album_id(self) -> str:
        dto = self._active_dto()
        return dto.id

    @typechecked
    def get_album_name(self) -> str:
        try:
            return self._active_dto().album_name
        except AttributeError:
            return ""

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
    def record_error(self, error_code: str, message: str) -> None:
        """Record an error event for this album and prune old entries.

        The window for pruning is taken from config `ALBUM_ERROR_WINDOW_SECONDS`.
        """
        try:
            import time

            from immich_autotag.albums.albums.album_error_entry import AlbumErrorEntry
            from immich_autotag.config.internal_config import ALBUM_ERROR_WINDOW_SECONDS

            now = time.time()
            self._error_history.append(
                AlbumErrorEntry(timestamp=now, code=error_code, message=str(message))
            )
            cutoff = now - int(ALBUM_ERROR_WINDOW_SECONDS)
            # Keep only recent entries
            self._error_history = [
                e for e in self._error_history if e.timestamp >= cutoff
            ]
        except Exception:
            # Never let recording errors raise and break higher-level flows
            pass

    @typechecked
    def error_count(self, window_seconds: int | None = None) -> int:
        try:
            import time

            from immich_autotag.config.internal_config import ALBUM_ERROR_WINDOW_SECONDS

            window = (
                int(window_seconds)
                if window_seconds is not None
                else int(ALBUM_ERROR_WINDOW_SECONDS)
            )
            cutoff = time.time() - window
            return sum(1 for e in self._error_history if e.timestamp >= cutoff)
        except Exception:
            return 0

    @typechecked
    def should_mark_unavailable(
        self, threshold: int | None = None, window_seconds: int | None = None
    ) -> bool:
        try:
            from immich_autotag.config.internal_config import ALBUM_ERROR_THRESHOLD

            th = int(threshold) if threshold is not None else int(ALBUM_ERROR_THRESHOLD)
            return self.error_count(window_seconds) >= th
        except Exception:
            return False

    @conditional_typechecked
    def reload_from_api(self, client: ImmichClient) -> None:
        """Reloads the album DTO from the API and clears the cache."""
        from immich_client import errors as immich_errors
        from immich_client.api.albums import get_album_info

        try:
            album_dto = get_album_info.sync(
                id=self.get_album_uuid_no_cache(), client=client
            )
            self._set_album_full(album_dto)
            self.invalidate_cache()
        except immich_errors.UnexpectedStatus as exc:
            try:
                dto_for_repr = self._active_dto()
                try:
                    album_name = dto_for_repr.album_name
                except AttributeError:
                    album_name = None
                    # Create a short, safe summary instead of using repr() which
                    # can emit very large DTO dumps (causing huge CI logs).
                    try:
                        try:
                            assets_attr = dto_for_repr.assets
                            asset_count = (
                                len(assets_attr) if assets_attr is not None else None
                            )
                        except Exception:
                            asset_count = None

                        try:
                            dto_id = dto_for_repr.id
                        except Exception:
                            dto_id = None

                        partial_repr = (
                            f"AlbumDTO(id={dto_id!r}, "
                            f"name={album_name!r}, assets={asset_count})"
                        )
                    except Exception:
                        partial_repr = "<unrepresentable album_partial>"
                except Exception:
                    partial_repr = "<unrepresentable album_partial>"
            except Exception:
                album_name = None
                partial_repr = "<unrepresentable album_partial>"

            # Determine HTTP status code when available. immich_client's
            # UnexpectedStatus may expose the code; fallback to parsing.
            try:
                status_code = exc.status_code
            except Exception:
                status_code = None
            if status_code is None:
                try:
                    msg = str(exc)
                    if (
                        "status code: 400" in msg
                        or "Unexpected status code: 400" in msg
                    ):
                        status_code = 400
                except Exception:
                    status_code = None

            # Handle 400 (Not found / no access) as a non-fatal condition:
            # mark album unavailable and continue. This prevents failing the
            # whole run when some albums are no longer accessible.
            if status_code == 400:
                # Record the recoverable error and decide whether to mark unavailable
                try:
                    self.record_error("HTTP_400", str(exc))
                except Exception:
                    pass

                # Log a concise warning including the current recent error count
                try:
                    current_count = self.error_count()
                except Exception:
                    current_count = None
                log(
                    (
                        f"[WARN] get_album_info returned 400 for album id="
                        f"{self.get_album_id()!r} name={album_name!r}. "
                        f"Recorded recoverable error (count={current_count}). "
                        f"album_partial={partial_repr}"
                    ),
                    level=LogLevel.WARNING,
                )

                # If the recent error count exceeds configured threshold,
                # mark unavailable
                try:
                    from immich_autotag.config.internal_config import (
                        ALBUM_ERROR_THRESHOLD,
                        ALBUM_ERROR_WINDOW_SECONDS,
                    )

                    if self.should_mark_unavailable(
                        ALBUM_ERROR_THRESHOLD, ALBUM_ERROR_WINDOW_SECONDS
                    ):
                        try:
                            self._unavailable = True
                        except Exception:
                            pass
                        # Clear any cached assets
                        self.invalidate_cache()
                        # Report the event to the modification report
                        try:
                            from immich_autotag.report.modification_report import (
                                ModificationReport,
                            )
                            from immich_autotag.tags.modification_kind import (
                                ModificationKind,
                            )

                            tag_mod_report = ModificationReport.get_instance()
                            tag_mod_report.add_error_modification(
                                kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
                                album=self,
                                error_message=partial_repr,
                                error_category="HTTP_400",
                                extra={"recent_errors": len(self._error_history)},
                            )
                        except Exception:
                            pass
                        # Notify the global collection about this album state change
                        try:
                            from immich_autotag.albums.albums.album_collection_wrapper import (
                                AlbumCollectionWrapper,
                            )

                            AlbumCollectionWrapper.get_instance().notify_album_marked_unavailable(
                                self
                            )
                        except Exception:
                            pass
                        return
                except Exception:
                    # If config lookup fails or check fails,
                    # be conservative and do not mark unavailable
                    pass
                # Otherwise, do not mark unavailable yet; continue without raising

            # Other unexpected statuses are treated as fatal and re-raised.
            log(
                (
                    (
                        f"[FATAL] get_album_info failed for album id={self.get_album_id()!r} "
                        f"name={album_name!r}. Exception: {exc!r}. "
                        f"album_partial={partial_repr}"
                    )
                ),
                level=LogLevel.ERROR,
            )
            raise

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
        assert self._album_full is not None
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
        tag_mod_report: "ModificationReport | None" = None,
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
            from immich_autotag.tags.modification_kind import ModificationKind

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

        from immich_autotag.config.internal_config import get_immich_web_base_url

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

        from immich_autotag.tags.modification_kind import ModificationKind

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
        found = False
        for item in result:
            try:
                _id = item.id
                _success = item.success
            except AttributeError:
                raise RuntimeError(
                    (
                        f"Item in add_assets_to_album response missing required attributes: "
                        f"{item}"
                    )
                )
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    try:
                        error_msg = item.error
                    except AttributeError:
                        error_msg = None
                    asset_url = asset_wrapper.get_immich_photo_url().geturl()
                    album_url = self.get_immich_album_url().geturl()
                    # If the error is 'duplicate', reactive refresh:
                    # reload album data from API.
                    # This detects that our cached album data is stale,
                    # and subsequent assets in this batch will benefit
                    # from the fresh data without additional API calls.
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
                    else:
                        raise RuntimeError(
                            (
                                f"Asset {asset_wrapper.id} was not successfully added to album "
                                f"{self.get_album_id()}: {error_msg}\n"
                                f"Asset link: {asset_url}\n"
                                f"Album link: {album_url}"
                            )
                        )
        if not found:
            raise RuntimeError(
                (
                    f"Asset {asset_wrapper.id} not found in add_assets_to_album response for album "
                    f"{self.get_album_id()}."
                )
            )
        tag_mod_report.add_assignment_modification(
            kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
            asset_wrapper=asset_wrapper,
            album=self,
        )
        # If requested, invalidate cache after operation and validate with retry logic
        self._verify_asset_in_album_with_retry(asset_wrapper, client, max_retries=3)

    @conditional_typechecked
    def remove_asset(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        tag_mod_report: "ModificationReport" = None,
    ) -> None:
        """
        Removes the asset from the album using the API and validates the result.

        Safe to call even if asset is not in album (idempotent operation).
        Raises exception only if the removal fails unexpectedly.
        """
        from immich_client.api.albums import remove_asset_from_album
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log
        from immich_autotag.tags.modification_kind import ModificationKind


        # Enforce safety: only allow removal from temporary or duplicate albums
        if not (self.is_temporary_album() or self.is_duplicate_album()):
            raise RuntimeError(
                f"Refusing to remove asset from album '{self.get_album_name()}' (id={self.get_album_id()}): not a temporary or duplicate album."
            )

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

        found = False
        from immich_autotag.config._internal_types import ErrorHandlingMode
        from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE

        for item in result:
            try:
                _id = item.id
                _success = item.success
            except AttributeError:
                raise RuntimeError(
                    f"Item in remove_assets_from_album response missing required attributes: "
                    f"{item}"
                )
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    try:
                        error_msg = item.error
                    except AttributeError:
                        error_msg = None
                    asset_url = asset_wrapper.get_immich_photo_url().geturl()
                    album_url = self.get_immich_album_url().geturl()
                    # Handle known recoverable errors as warnings or errors depending on mode
                    if error_msg and (
                        str(error_msg).lower() in ("not_found", "no_permission")
                    ):
                        if str(error_msg).lower() == "not_found":
                            # Album is gone, notify AlbumCollectionWrapper singleton to remove it from collection
                            try:
                                from immich_autotag.albums.albums.album_collection_wrapper import (
                                    AlbumCollectionWrapper,
                                )

                                collection = AlbumCollectionWrapper.get_instance()
                                removed = collection.remove_album_local(self)
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
                                    f"[ALBUM REMOVAL] Asset {asset_wrapper.id} could not be removed from album "
                                    f"{self.get_album_id()}: {error_msg}\n"
                                    f"Asset link: {asset_url}\n"
                                    f"Album link: {album_url}"
                                ),
                                level=LogLevel.WARNING,
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

        if not found:
            log(
                (
                    f"[ALBUM REMOVAL] Asset {asset_wrapper.id} not found in remove_assets_from_album "
                    f"response for album {self.get_album_id()}. Treating as already removed."
                ),
                level=LogLevel.WARNING,
            )
            if DEFAULT_ERROR_MODE != ErrorHandlingMode.DEVELOPMENT:
                return

            raise RuntimeError(
                (
                    f"Asset {asset_wrapper.id} not found in remove_assets_from_album response for album "
                    f"{self.get_album_id()}."
                )
            )

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
            tag_mod_report.add_assignment_modification(
                kind=ModificationKind.REMOVE_ASSET_FROM_ALBUM,
                asset_wrapper=asset_wrapper,
                album=self,
            )

        # Invalidate cache and verify removal with retry logic
        self._verify_asset_removed_from_album_with_retry(
            asset_wrapper, client, max_retries=3
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
                        f"{self.get_album_id()}. "
                        f"This may be an eventual consistency or API issue."
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
                        f"{self.get_album_id()}. "
                        f"This may be an eventual consistency or API issue."
                    ),
                    level=LogLevel.WARNING,
                )

    @staticmethod
    @conditional_typechecked
    def from_id(
        client: ImmichClient,
        album_id: UUID,
        tag_mod_report: ModificationReport | None = None,
    ) -> "AlbumResponseWrapper":
        """
        Gets an album by ID, wraps it, and trims the name if necessary.
        """

        from immich_client.api.albums import get_album_info

        album_full = get_album_info.sync(id=album_id, client=client)
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
        tag_mod_report: ModificationReport | None = None,
    ) -> "AlbumResponseWrapper":
        """
        Create an AlbumResponseWrapper from a partial DTO.

        The wrapper will store the provided DTO as `_album_partial` and
        will not populate the full cache. Callers must explicitly request
        loading the full DTO via `ensure_full`/`reload_from_api`.
        """
        wrapper = AlbumResponseWrapper(album_partial=dto)
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

    @staticmethod
    def from_dto(*_args, **_kwargs) -> "AlbumResponseWrapper":
        """
        Ambiguous constructor intentionally removed. Use `from_partial_dto`
        or `from_full_dto` to make representation explicit.
        """
        raise RuntimeError(
            (
                "Use AlbumResponseWrapper.from_partial_dto or from_full_dto; "
                "from_dto is ambiguous"
            )
        )
