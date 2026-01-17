from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import ParseResult

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto

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

    album_partial: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )
    _album_full: AlbumResponseDto | None = attrs.field(default=None, init=False)

    @property
    def album(self) -> AlbumResponseDto:
        """Returns full album if loaded, otherwise partial. Lazy-loads full data on first detailed access."""
        return self._album_full if self._album_full is not None else self.album_partial

    @album.setter
    def album(self, value: AlbumResponseDto) -> None:
        """Sets the full album data."""
        self._album_full = value

    def _ensure_full_album_loaded(self, client: ImmichClient) -> None:
        """Lazy-loads full album data from API if not already loaded."""
        if self._album_full is not None:
            return
        from immich_client.api.albums import get_album_info

        self._album_full = get_album_info.sync(id=self.album_partial.id, client=client)

    from functools import cached_property

    @cached_property
    def asset_ids(self) -> set[str]:
        """Set of album asset IDs, cached for O(1) access in has_asset.
        Assets are already populated by from_client() or reload_from_api()."""
        return set(a.id for a in self.album.assets) if self.album.assets else set()

    @conditional_typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        """Returns True if the asset belongs to this album (optimized with set)."""
        return asset.id in self.asset_ids

    @conditional_typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        """Returns True if the wrapped asset belongs to this album (high-level API).
        If use_cache=True, uses the cached set (fast). If False, uses linear search (slow, for testing only).
        """
        if use_cache:
            return asset_wrapper.asset.id in self.asset_ids
        else:
            return self.has_asset(asset_wrapper.asset)

    @conditional_typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        """
        Returns the album's assets wrapped in AssetResponseWrapper, using the asset_manager from the context.
        """
        if not self.album.assets:
            return []
        return [
            context.asset_manager.get_wrapper_for_asset(a, context)
            for a in self.album.assets
        ]

    from typing import Optional

    # from immich_client.client import Client (already imported at top)
    from immich_autotag.report.modification_report import ModificationReport

    @conditional_typechecked
    def trim_name_if_needed(
        self,
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        """
        If the album name starts with a space, trim it and update via API. Optionally logs the change.
        """
        if self.album.album_name.startswith(" "):
            cleaned_name = self.album.album_name.strip()
            from immich_client.api.albums import update_album_info
            from immich_client.models.update_album_dto import UpdateAlbumDto

            update_body = UpdateAlbumDto(album_name=cleaned_name)
            # update_album_info.sync expects id as UUID and client as AuthenticatedClient
            from uuid import UUID

            update_album_info.sync(
                id=UUID(self.album.id),
                client=client,  # FIXME: should be AuthenticatedClient if available
                body=update_body,
            )
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report.add_album_modification(
                kind=ModificationKind.RENAME_ALBUM,
                album=self,
                old_value=self.album.album_name,
                new_value=cleaned_name,
            )
            log(
                f"Album '{self.album.album_name}' renamed to '{cleaned_name}'",
                level=LogLevel.INFO,
            )

    @conditional_typechecked
    def get_immich_album_url(self) -> "ParseResult":
        """
        Returns the Immich web URL for this album as ParseResult.
        """
        from urllib.parse import urlparse

        from immich_autotag.config.internal_config import get_immich_web_base_url

        # Assume album URL is /albums/<id>
        url = f"{get_immich_web_base_url()}/albums/{self.album.id}"
        return urlparse(url)

    @conditional_typechecked
    def add_asset(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: ImmichClient,
        tag_mod_report: "ModificationReport",
    ) -> None:
        """
        Adds the asset to the album using the API and validates the result. Raises exception if it fails.
        tag_mod_report is mandatory and always required to track all modifications.
        """
        from immich_client.api.albums import add_assets_to_album
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        from immich_autotag.tags.modification_kind import ModificationKind

        # Avoid adding if already present
        if asset_wrapper.id in [a.id for a in self.album.assets or []]:
            return
        result = add_assets_to_album.sync(
            id=self.album.id,
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
                            f"Asset {asset_wrapper.id} already in album {self.album.id} (detected stale cache). "
                            f"Reloading album data for subsequent operations.",
                            level=LogLevel.INFO,
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
                            f"Asset {asset_wrapper.id} was not successfully added to album {self.album.id}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}"
                        )
        if not found:
            raise RuntimeError(
                f"Asset {asset_wrapper.id} not found in add_assets_to_album response for album {self.album.id}."
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
        from immich_client.api.albums import remove_assets_from_album
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log
        from immich_autotag.tags.modification_kind import ModificationKind

        # Check if asset is in album first
        if asset_wrapper.id not in [a.id for a in self.album.assets or []]:
            log(
                f"[ALBUM REMOVAL] Asset {asset_wrapper.id} is not in album {self.album.id}, skipping removal.",
                level=LogLevel.DEBUG,
            )
            return

        # Remove asset from album
        result = remove_assets_from_album.sync(
            id=self.album.id,
            client=client,
            body=BulkIdsDto(ids=[asset_wrapper.id]),
        )

        # Validate the result
        if not isinstance(result, list):
            raise RuntimeError(
                f"remove_assets_from_album did not return a list, got {type(result)}"
            )

        found = False
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
                    raise RuntimeError(
                        f"Asset {asset_wrapper.id} was not successfully removed from album {self.album.id}: {error_msg}\nAsset link: {asset_url}\nAlbum link: {album_url}"
                    )

        if not found:
            raise RuntimeError(
                f"Asset {asset_wrapper.id} not found in remove_assets_from_album response for album {self.album.id}."
            )

        # Log successful removal
        log(
            f"[ALBUM REMOVAL] Asset {asset_wrapper.id} removed from album {self.album.id} ('{self.album.album_name}').",
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
        client: Client,
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
                    f"After {max_retries} retries, asset {asset_wrapper.id} does NOT appear in album {self.album.id}. "
                    f"This may be an eventual consistency or API issue.",
                    level=LogLevel.WARNING,
                )

    @conditional_typechecked
    def _verify_asset_removed_from_album_with_retry(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: Client,
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
                    f"After {max_retries} retries, asset {asset_wrapper.id} still appears in album {self.album.id}. "
                    f"This may be an eventual consistency or API issue.",
                    level=LogLevel.WARNING,
                )

    def invalidate_cache(self) -> None:
        """Invalidates all cached properties for this album wrapper (currently only asset_ids)."""
        if hasattr(self, "asset_ids"):
            try:
                del self.asset_ids
            except Exception:
                pass

    @conditional_typechecked
    def reload_from_api(self, client: Client) -> None:
        """Reloads the album DTO from the API and clears the cache."""
        from immich_client.api.albums import get_album_info

        album_dto = get_album_info.sync(id=self.album_partial.id, client=client)
        self.album = album_dto  # Use property setter
        self.invalidate_cache()

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
        wrapper = AlbumResponseWrapper(album_partial=album_full)
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
        wrapper = AlbumResponseWrapper(album_partial=dto)
        return wrapper
