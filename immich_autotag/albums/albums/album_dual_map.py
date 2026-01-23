from typing import Iterable

import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_map import AlbumMap
from immich_autotag.albums.albums.album_name_map import AlbumNameMap


@attrs.define(auto_attribs=True, slots=True)
class AlbumDualMap:
    """
    Encapsulates both AlbumMap (by UUID) and AlbumNameMap (by name).
    Ensures both are updated together and provides efficient access.
    Uses attrs for validation and robustness.
    """

    _id_map: AlbumMap = attrs.field(factory=AlbumMap)
    _name_map: AlbumNameMap = attrs.field(factory=AlbumNameMap)

    from typeguard import typechecked

    @typechecked
    def add(self, album: AlbumResponseWrapper):
        self._id_map.append(album)
        self._name_map.add(album)

    @typechecked
    def remove(self, album: AlbumResponseWrapper):
        self._id_map.remove(album)
        self._name_map.remove(album)

    @typechecked
    def get_by_id(self, uuid: str) -> AlbumResponseWrapper:
        # Defensive: raise if not found
        from uuid import UUID

        try:
            uuid_obj = UUID(uuid)
        except Exception:
            raise RuntimeError(f"Invalid UUID string: {uuid}")
        return self._id_map.get_by_uuid(uuid_obj)

    @typechecked
    def get_by_name(self, name: str) -> AlbumResponseWrapper:
        return self._name_map.get(name)

    @typechecked
    def clear(self):
        self._id_map.clear()
        self._name_map.clear()

    @typechecked
    def all(self) -> Iterable[AlbumResponseWrapper]:
        return self._id_map._albums.values()

    @typechecked
    def __len__(self):
        return len(self._id_map)
