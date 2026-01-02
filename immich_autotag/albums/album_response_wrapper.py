from __future__ import annotations

from typing import TYPE_CHECKING

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
        """Set de IDs de assets del álbum, cacheado para acceso O(1) en has_asset."""
        return set(a.id for a in self.album.assets) if self.album.assets else set()

    @typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        """Returns True if the asset belongs to this album (optimizado con set)."""
        return asset.id in self.asset_ids

    @typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        """Returns True if the wrapped asset belongs to this album (high-level API).
        Si use_cache=True, usa el set cacheado (rápido). Si False, usa búsqueda lineal (lento, solo para pruebas).
        """
        if use_cache:
            return asset_wrapper.asset.id in self.asset_ids
        else:
            return self.has_asset(asset_wrapper.asset)

    @typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        """
        Returns the album's assets wrapped in AssetResponseWrapper, usando el asset_manager del contexto.
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
                old_name=self.album.album_name,
                new_name=cleaned_name,
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
        Devuelve la URL web de Immich para este álbum como ParseResult.
        """
        from urllib.parse import urlparse

        from immich_autotag.config.internal_config import IMMICH_WEB_BASE_URL

        # Suponemos que la URL de álbum es /albums/<id>
        url = f"{IMMICH_WEB_BASE_URL}/albums/{self.album.id}"
        return urlparse(url)
