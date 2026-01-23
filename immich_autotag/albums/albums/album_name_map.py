from typing import Dict

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class AlbumNameMap:
    """
    Efficient mapping from album name (str) to AlbumResponseWrapper.
    Uses attrs for validation and robustness.
    """

    _name_to_album: Dict[str, AlbumResponseWrapper] = attrs.field(factory=dict)

    @typechecked
    def add(self, album: AlbumResponseWrapper):
        name = album.get_album_name()
        if name in self._name_to_album:
            raise RuntimeError(
                f"Album with name '{name}' already exists in AlbumNameMap."
            )
        self._name_to_album[name] = album

    @typechecked
    def remove(self, album: AlbumResponseWrapper):
        name = album.get_album_name()
        if name not in self._name_to_album:
            raise RuntimeError(
                f"Cannot remove: album with name '{name}' does not exist in AlbumNameMap."
            )
        del self._name_to_album[name]

    @typechecked
    def get(self, name: str) -> AlbumResponseWrapper:
        if name not in self._name_to_album:
            raise RuntimeError(
                f"Album with name '{name}' does not exist in AlbumNameMap."
            )
        return self._name_to_album[name]

    @typechecked
    def clear(self):
        self._name_to_album.clear()

    @typechecked
    def values(self):
        return self._name_to_album.values()

    @typechecked
    def __contains__(self, name: str) -> bool:
        return name in self._name_to_album

    @typechecked
    def __len__(self):
        return len(self._name_to_album)
