from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import ParseResult

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.types import ImmichClient

if TYPE_CHECKING:
    from immich_autotag.report.modification_report import ModificationReport

from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log


@attrs.define(auto_attribs=True, slots=True)
class AlbumResponseWrapper:

    _album_partial: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )
    _album_full: AlbumResponseDto | None = attrs.field(default=None, init=False)
    # Explicit cache for asset ids. Use get_asset_ids() to access.
    _asset_ids_cache: set[str] | None = attrs.field(default=None, init=False)

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
        return self._album_partial.id

    @typechecked
    def get_album_name(self) -> str:
        return getattr(self._album_partial, "album_name", "")

    @typechecked
    def get_album_uuid(self)-> "UUID":
        from uuid import UUID

        return UUID(self._album_partial.id)

    @typechecked
    def ensure_full(self) -> None:
        if not self.is_full:
            self.reload_from_api(self.get_default_client())

    def _get_partial(self) -> AlbumResponseDto:
        return self._album_partial

    def _get_full(self) -> AlbumResponseDto:
        return self._get_album_full_or_load()

    @typechecked
    def _set_album_full(self, value: AlbumResponseDto) -> None:
        self._album_full = value

    def invalidate_cache(self) -> None:
        try:
            self._asset_ids_cache = None
        except Exception:
            pass

    @conditional_typechecked
    def reload_from_api(self, client: ImmichClient) -> None:
        """Reloads the album DTO from the API and clears the cache."""
        from immich_client import errors as immich_errors
        from immich_client.api.albums import get_album_info

        try:
            album_dto = get_album_info.sync(id=self._album_partial.id, client=client)
            self._set_album_full(album_dto)
            self.invalidate_cache()
        except immich_errors.UnexpectedStatus as exc:
            try:
                album_name = getattr(self._album_partial, "album_name", None)
                partial_repr = repr(self._album_partial)
            except Exception:
                album_name = None
                partial_repr = "<unrepresentable album_partial>"

            log(
                (
                    f"[FATAL] get_album_info failed for album id={self._album_partial.id!r} "
                    f"name={album_name!r}. Exception: {exc!r}. "
                    f"album_partial={partial_repr}"
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
        if not (self._album_partial.assets):
            return []
        return [
            context.asset_manager.get_wrapper_for_asset(a, context)
            for a in self._get_album_full_or_load().assets
        ]

    from typing import Optional

    from immich_autotag.report.modification_report import ModificationReport

    @conditional_typechecked
    def trim_name_if_needed(
        self,
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        album_name = getattr(self._album_partial, "album_name", "")
        if album_name.startswith(" "):
            cleaned_name = album_name.strip()
            from immich_client.api.albums import update_album_info
            from immich_client.models.update_album_dto import UpdateAlbumDto

            update_body = UpdateAlbumDto(album_name=cleaned_name)
            from uuid import UUID

            update_album_info.sync(
                id=UUID(self._album_partial.id),
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
            log(f"Album '{album_name}' renamed to '{cleaned_name}'", level=LogLevel.FOCUS)

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
        from immich_client.api.albums import add_assets_to_album
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        from immich_autotag.tags.modification_kind import ModificationKind

        # Avoid adding if already present
        if asset_wrapper.id in [a.id for a in (self._album_partial.assets or [])]:
            return
        result = add_assets_to_album.sync(
            id=self._album_partial.id,
            client=client,
            body=BulkIdsDto(ids=[asset_wrapper.id]),
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
                    f"Item in add_assets_to_album response missing required attributes: {item}"
                )
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    error_msg = getattr(item, "error", None)
                    asset_url = asset_wrapper.get_immich_photo_url().geturl()
                    album_url = self.get_immich_album_url().geturl()
                    # If the error is 'duplicate', reactive refresh: reload album data from API
                    # This detects that our cached album data is stale, and subsequent assets in this
                    # batch will benefit from the fresh data without additional API calls
                    if error_msg and "duplicate" in str(error_msg).lower():
                        log(
                            f"Asset {asset_wrapper.id} already in album {self.get_album_id()} (detected stale cache). "
                            f"Reloading album data for subsequent operations.",
                            level=LogLevel.FOCUS,
                        )
                        # Reactive refresh: reload album from API to get fresh data
                        # This ensures subsequent assets see current state without preventive reloads
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
                            },
                        )
                        return
                    else:
                        raise RuntimeError(
                            f"Asset {asset_wrapper.id} was not successfully added to album {self.get_album_id()}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}"
                        )
        if not found:
            raise RuntimeError(
                f"Asset {asset_wrapper.id} not found in add_assets_to_album response for album {self.get_album_id()}."
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

        # Check if asset is in album first
        if asset_wrapper.id not in [a.id for a in (self._album_partial.assets or [])]:
            log(
                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} is not in album {self._album_partial.id}, skipping removal.",
                level=LogLevel.DEBUG,
            )
            return

        # Remove asset from album
        result = remove_asset_from_album.sync(
            id=self._album_partial.id,
            client=client,
            body=BulkIdsDto(ids=[asset_wrapper.id]),
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
                    f"Item in remove_assets_from_album response missing required attributes: {item}"
                )
            if _id == str(asset_wrapper.id):
                found = True
                if not _success:
                    error_msg = getattr(item, "error", None)
                    asset_url = asset_wrapper.get_immich_photo_url().geturl()
                    album_url = self.get_immich_album_url().geturl()
                    # Handle known recoverable errors as warnings or errors depending on mode
                    if error_msg and (
                        str(error_msg).lower() in ("not_found", "no_permission")
                    ):
                        if str(error_msg).lower() == "not_found":
                            # Album is gone, notify AlbumCollectionWrapper singleton to remove it from collection
                            try:
                                from immich_autotag.albums.album_collection_wrapper import (
                                    AlbumCollectionWrapper,
                                )

                                collection = AlbumCollectionWrapper.get_instance()
                                removed = collection.remove_album_local(self)
                                log(
                                    f"[ALBUM REMOVAL] Album {self._album_partial.id} ('{self.get_album_name()}') removed from collection due to not_found error during asset removal.",
                                    level=LogLevel.FOCUS,
                                )
                            except Exception as e:
                                log(
                                    f"[ALBUM REMOVAL] Failed to remove album {self._album_partial.id} from collection after not_found: {e}",
                                    level=LogLevel.WARNING,
                                )
                            log(
                                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} could not be removed from album {self.get_album_id()}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}",
                                level=LogLevel.WARNING,
                            )
                            return
                        if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                            raise RuntimeError(
                                f"Asset {asset_wrapper.id} was not successfully removed from album {self.get_album_id()}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}"
                            )
                        else:
                            log(
                                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} could not be removed from album {self.get_album_id()}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}",
                                level=LogLevel.WARNING,
                            )
                            return
                    # Otherwise, treat as fatal
                    raise RuntimeError(
                        f"Asset {asset_wrapper.id} was not successfully removed from album {self.get_album_id()}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}"
                    )

        if not found:
            log(
                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} not found in remove_assets_from_album response for album {self._album_partial.id}. Treating as already removed.",
                level=LogLevel.WARNING,
            )
            if DEFAULT_ERROR_MODE != ErrorHandlingMode.DEVELOPMENT:
                return

            raise RuntimeError(
                f"Asset {asset_wrapper.id} not found in remove_assets_from_album response for album {self._album_partial.id}."
            )

        # Log successful removal
        log(
            f"[ALBUM REMOVAL] Asset {asset_wrapper.id} removed from album {self._album_partial.id} ('{self.get_album_name()}').",
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
            if self.has_asset(asset_wrapper.asset):
                return  # Success - asset is in album

            if attempt < max_retries - 1:
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                wait_time = 0.1 * (2**attempt)
                time.sleep(wait_time)
            else:
                log(
                    f"After {max_retries} retries, asset {asset_wrapper.id} does NOT appear in album {self._album_partial.id}. "
                    f"This may be an eventual consistency or API issue.",
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
            if not self.has_asset(asset_wrapper.asset):
                return  # Success - asset is no longer in album

            if attempt < max_retries - 1:
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                wait_time = 0.1 * (2**attempt)
                time.sleep(wait_time)
            else:
                log(
                    f"After {max_retries} retries, asset {asset_wrapper.id} still appears in album {self._album_partial.id}. "
                    f"This may be an eventual consistency or API issue.",
                    level=LogLevel.WARNING,
                )

    @staticmethod
    @conditional_typechecked
    def from_id(
        client: ImmichClient,
        album_id: str,
        tag_mod_report: ModificationReport | None = None,
    ) -> "AlbumResponseWrapper":
        """
        Gets an album by ID, wraps it, and trims the name if necessary.
        """
        from immich_client.api.albums import get_album_info

        album_full = get_album_info.sync(id=album_id, client=client)
        wrapper = AlbumResponseWrapper(_album_partial=album_full)
        wrapper._album_full = album_full
        wrapper.trim_name_if_needed(client=client, tag_mod_report=tag_mod_report)
        return wrapper

    @staticmethod
    @conditional_typechecked
    def from_dto(
        dto: AlbumResponseDto,
        tag_mod_report: ModificationReport | None = None,
    ) -> "AlbumResponseWrapper":
        """
        Creates an AlbumResponseWrapper from a DTO without making API calls.
        Uses album_partial to enable lazy-loading of full data on first access.
        """
        wrapper = AlbumResponseWrapper(_album_partial=dto)
        return wrapper
