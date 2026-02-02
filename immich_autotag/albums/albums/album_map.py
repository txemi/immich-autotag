from typing import Iterator

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.types.uuid_wrappers import AlbumUUID


@attrs.define(auto_attribs=True, slots=True)
class AlbumMap:
    """
    Stores albums in a dict keyed by UUID. Prevents duplicates.
    """

    _albums: dict[AlbumUUID, AlbumResponseWrapper] = attrs.field(
        factory=dict,
        repr=lambda value: f"size={len(value)}",
    )

    @typechecked
    def get_by_uuid(self, uuid: AlbumUUID) -> AlbumResponseWrapper:
        if uuid not in self._albums:
            raise RuntimeError(f"Album with uuid {uuid} does not exist in AlbumMap")
        return self._albums[uuid]

    @typechecked
    def append(self, album: AlbumResponseWrapper):
        album_id = album.get_album_uuid()
        if album_id in self._albums:
            raise ValueError(f"Album with uuid {album_id} already exists in AlbumMap")
        self._albums[album_id] = album

    @typechecked
    def remove(self, album: AlbumResponseWrapper):
        album_id = album.get_album_uuid()
        if album_id in self._albums:
            self._albums[album_id].mark_deleted()
        else:
            raise ValueError(f"Album with uuid {album_id} not found in AlbumMap")

    def to_list(self) -> list[AlbumResponseWrapper]:
        return list(self._albums.values())

    def clear(self):
        self._albums.clear()

    def __getitem__(self, uuid: AlbumUUID) -> AlbumResponseWrapper:
        return self._albums[uuid]

    @typechecked
    def __iter__(self) -> Iterator[AlbumResponseWrapper]:
        return iter(self._albums.values())

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album.get_album_uuid() in self._albums

    @typechecked
    def __len__(self) -> int:
        return len(self._albums)

    def __bool__(self):
        return bool(self._albums)
