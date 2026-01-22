from typing import Iterator
from uuid import UUID
import attrs
from typeguard import typechecked
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

@attrs.define(auto_attribs=True, slots=True)
class AlbumMap:
    """
    Stores albums in a dict keyed by UUID. Prevents duplicates.
    """
    _albums: dict[UUID, AlbumResponseWrapper] = attrs.field(factory=dict)

    @typechecked
    def get_by_uuid(self, uuid: UUID) -> AlbumResponseWrapper | None:
        return self._albums.get(uuid)

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

    def __iter__(self) -> Iterator[AlbumResponseWrapper]:
        return iter(self._albums.values())

    def __len__(self) -> int:
        return len(self._albums)

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album.get_album_uuid() in self._albums

    def to_list(self) -> list[AlbumResponseWrapper]:
        return list(self._albums.values())

    def clear(self):
        self._albums.clear()

    def __bool__(self):
        return bool(self._albums)

    def __getitem__(self, uuid: UUID) -> AlbumResponseWrapper:
        return self._albums[uuid]

    def __repr__(self):
        return f"AlbumMap({self._albums!r})"
