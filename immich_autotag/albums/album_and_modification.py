from __future__ import annotations

import attrs
from typeguard import typechecked

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_entries_list import ModificationEntriesList


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumAndModification:
    _album: AlbumResponseWrapper
    _modifications: ModificationEntriesList

    @typechecked
    def get_album(self) -> AlbumResponseWrapper:
        return self._album

    @typechecked
    def get_modifications(self) -> ModificationEntriesList:
        return self._modifications

    @staticmethod
    @typechecked
    def combine_optional(
        first: AlbumAndModification | None,
        second: AlbumAndModification | None,
    ) -> AlbumAndModification | None:
        if first is None and second is None:
            return None
        if first is None:
            return second
        if second is None:
            return first
        # Combine modifications, keep album from first (or second, as needed)
        return AlbumAndModification(
            album=first.get_album(),
            modifications=ModificationEntriesList.combine_optional(
                first.get_modifications(), second.get_modifications()
            ),
        )
