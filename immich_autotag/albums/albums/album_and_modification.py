from typing import Optional

import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_entry import ModificationEntry


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumAndModification:
    album: Optional[AlbumResponseWrapper] = None
    modification: Optional[ModificationEntry] = None

    @staticmethod
    def from_album(album: Optional[AlbumResponseWrapper]) -> "AlbumAndModification":
        """
        Static constructor for the common case where only the album is provided.
        Internally uses an empty ModificationEntriesList or None as appropriate.
        """
        return AlbumAndModification(album=album, modification=None)

    @staticmethod
    def from_album_and_entry(
        album: Optional[AlbumResponseWrapper], entry: Optional[ModificationEntry]
    ) -> "AlbumAndModification":
        """
        Static constructor for the common case where only one modification entry is present.
        """
        return AlbumAndModification(album=album, modification=entry)

    @staticmethod
    def empty() -> "AlbumAndModification":
        """
        Static constructor for the case where both album and modification are empty.
        """
        return AlbumAndModification(album=None, modification=None)
