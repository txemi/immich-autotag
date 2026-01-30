from typing import Iterator

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.types.uuid_wrappers import AlbumUUID


@attrs.define(auto_attribs=True, slots=True)
class AlbumList:

    _albums: list[AlbumResponseWrapper] = attrs.field(factory=list)

    @typechecked
    def get_by_uuid(self, uuid: AlbumUUID) -> AlbumResponseWrapper | None:
        """
        Returns the album with the given UUID (UUID or AlbumUUID), or None if not found.
        """
        # Always compare as UUID
        uuid_val = uuid.to_uuid()

        for album in self._albums:
            if album.get_album_uuid() == uuid_val:
                return album
        return None

    @typechecked
    def append(self, album: AlbumResponseWrapper):
        if album in self._albums:
            raise ValueError("Album already in AlbumList (no uuid)")
        album_id = album.get_album_uuid()
        if self.get_by_uuid(album_id) is not None:
            raise ValueError(f"Album with uuid {album_id} already in AlbumList")

        self._albums.append(album)

    def remove(self, album: AlbumResponseWrapper):
        self._albums.remove(album)

    def to_list(self) -> list[AlbumResponseWrapper]:
        return list(self._albums)

    def clear(self):
        self._albums.clear()

    @typechecked
    def remove_album(self, album: AlbumResponseWrapper):
        """Remove the first occurrence of album from the list (if present)."""
        try:
            self._albums.remove(album)
        except ValueError:
            pass  # If not present, do nothing

    def __getitem__(self, idx: int) -> AlbumResponseWrapper:
        return self._albums[idx]

    def __iter__(self) -> Iterator[AlbumResponseWrapper]:
        return iter(self._albums)

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album in self._albums

    def __len__(self) -> int:
        return len(self._albums)

    def __bool__(self):
        return bool(self._albums)

    def __repr__(self):
        return f"AlbumList({self._albums!r})"
