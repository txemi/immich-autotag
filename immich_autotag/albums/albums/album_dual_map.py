from typing import Iterable

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_map import AlbumMap
from immich_autotag.albums.albums.album_name_map import AlbumNameMap
from immich_autotag.types.uuid_wrappers import AlbumUUID


@attrs.define(auto_attribs=True, slots=True)
class AlbumDualMap:
    """
    Encapsulates both AlbumMap (by UUID) and AlbumNameMap (by name).
    Ensures both are updated together and provides efficient access.
    Uses attrs for validation and robustness.
    """

    _id_map: AlbumMap = attrs.field(factory=AlbumMap)
    _name_map: AlbumNameMap = attrs.field(factory=AlbumNameMap)

    @typechecked
    def add(self, album: AlbumResponseWrapper):
        self._id_map.append(album)
        self._name_map.add(album)

    @typechecked
    def remove(self, album: AlbumResponseWrapper):
        self._id_map.remove(album)
        self._name_map.remove(album)

    @typechecked
    def get_by_id(self, uuid: AlbumUUID) -> AlbumResponseWrapper:
        # Defensive: raise if not found

        return self._id_map.get_by_uuid(uuid)

    @typechecked
    def get_by_name(self, name: str) -> AlbumResponseWrapper | None:
        """
        Returns the AlbumResponseWrapper for the given name, or None if not found.
        """
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
