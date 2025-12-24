from __future__ import annotations

import attrs
from typeguard import typechecked

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumCollectionWrapper:
    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    @typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[str]:
        """Returns the names of the albums the asset belongs to."""
        album_names = []
        for album_wrapper in self.albums:
            if album_wrapper.has_asset(asset):
                album_names.append(album_wrapper.album.album_name)
        return album_names
