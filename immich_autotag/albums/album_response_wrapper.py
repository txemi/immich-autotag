from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import ParseResult

import attrs
from immich_client.client import Client
from immich_client.models.album_response_dto import AlbumResponseDto

if TYPE_CHECKING:
    from immich_autotag.report.modification_report import ModificationReport

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumResponseWrapper:

    album: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )

    from functools import cached_property

    @cached_property
    def asset_ids(self) -> set[str]:
        """Set of album asset IDs, cached for O(1) access in has_asset."""
        return set(a.id for a in self.album.assets) if self.album.assets else set()

    @typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        """Returns True if the asset belongs to this album (optimized with set)."""
        return asset.id in self.asset_ids

    @typechecked
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

    @typechecked
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

    @typechecked
    def trim_name_if_needed(
        self,
        client: Client,
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
            # Actually update the name in the DTO (if mutable)
            try:
                object.__setattr__(self.album, "album_name", cleaned_name)
            except Exception:
                pass
            print(f"Renamed album '{self.album.album_name}' to '{cleaned_name}'")

    @typechecked
    def get_immich_album_url(self) -> "ParseResult":
        """
        Returns the Immich web URL for this album as ParseResult.
        """
        from urllib.parse import urlparse

        from immich_autotag.config.internal_config import get_immich_web_base_url

        # Assume album URL is /albums/<id>
        url = f"{get_immich_web_base_url()}/albums/{self.album.id}"
        return urlparse(url)

    @typechecked
    def add_asset(
        self,
        asset_wrapper: "AssetResponseWrapper",
        client: Client,
        tag_mod_report: "ModificationReport" = None,
    ) -> None:
        """
        Adds the asset to the album using the API and validates the result. Raises exception if it fails.
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
                    # If the error is 'duplicate', only warning and log
                    if error_msg and "duplicate" in str(error_msg).lower():
                        warning_msg = f"[WARN] Asset {asset_wrapper.id} is already in album {self.album.id}: duplicate\nAsset link: {asset_url}\nAlbum link: {album_url}"
                        print(warning_msg)
                        from immich_autotag.tags.modification_kind import (
                            ModificationKind,
                        )

                        if tag_mod_report:
                            tag_mod_report.add_assignment_modification(
                                kind=ModificationKind.WARNING_ASSET_ALREADY_IN_ALBUM,
                                asset_wrapper=asset_wrapper,
                                album=self,
                                extra={
                                    "error": error_msg,
                                    "asset_url": asset_url,
                                    "album_url": album_url,
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
        if tag_mod_report:
            tag_mod_report.add_assignment_modification(
                kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
                asset_wrapper=asset_wrapper,
                album=self,
            )
        # If requested, invalidate cache after operation
        self.reload_from_api(client)
        self.invalidate_cache()
        # Check that the asset is really in the album after reloading
        if not self.has_asset(asset_wrapper.asset):
            print(
                f"[WARN] After reloading the album from the API, asset {asset_wrapper.id} does NOT appear in album {self.album.id}. This may be an eventual consistency or API issue."
            )

    def invalidate_cache(self):
        """Invalidates all cached properties for this album wrapper (currently only asset_ids)."""
        if hasattr(self, "asset_ids"):
            try:
                del self.asset_ids
            except Exception:
                pass

    def reload_from_api(self, client: Client):
        """Reloads the album DTO from the API and clears the cache."""
        from immich_client.api.albums import get_album_info

        album_dto = get_album_info.sync(id=self.album.id, client=client)
        object.__setattr__(self, "album", album_dto)
        self.invalidate_cache()

    from typeguard import typechecked

    @staticmethod
    @typechecked
    def from_id(
        client: "Client",
        album_id: str,
        tag_mod_report: "ModificationReport | None" = None,
    ) -> "AlbumResponseWrapper":
        """
        Gets an album by ID, wraps it, and trims the name if necessary.
        """
        from immich_client.api.albums import get_album_info

        album_full = get_album_info.sync(id=album_id, client=client)
        wrapper = AlbumResponseWrapper(album=album_full)
        wrapper.trim_name_if_needed(client=client, tag_mod_report=tag_mod_report)
        return wrapper
