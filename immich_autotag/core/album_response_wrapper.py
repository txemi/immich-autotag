from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_client.models.asset_response_dto import AssetResponseDto
    from .asset_response_wrapper import AssetResponseWrapper
from .immich_context import ImmichContext





@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumResponseWrapper:
    album: AlbumResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseDto)
    )

    @typechecked
    def has_asset(self, asset: AssetResponseDto) -> bool:
        """Returns True if the asset belongs to this album."""
        if self.album.assets:
            return any(a.id == asset.id for a in self.album.assets)
        return False

    @typechecked
    def wrapped_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        """
        Returns the album's assets wrapped in AssetResponseWrapper.
        """
        return (
            [AssetResponseWrapper(asset=a, context=context) for a in self.album.assets]
            if self.album.assets
            else []
        )
