from typing import Iterator

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class AlbumList:

    _albums: list[AlbumResponseWrapper] = attrs.field(factory=list)

    @typechecked
    def get_by_uuid(self, uuid: str) -> AlbumResponseWrapper | None:
        for album in self._albums:
            if album.get_album_id() == uuid:
                return album
        return None

    @typechecked
    def append(self, album: AlbumResponseWrapper):
        if album in self._albums:
            raise ValueError("Album already in AlbumList (no uuid)")
        album_id = album.get_album_id()
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
