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

    _name_to_album: Dict[str, AlbumResponseWrapper] = attrs.field(
        factory=dict,
        repr=lambda value: f"size={len(value)}",
    )

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
    def get(self, name: str) -> AlbumResponseWrapper | None:
        """
        Returns the AlbumResponseWrapper for the given name, or None if not found.
        """
        return self._name_to_album.get(name)

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
    @typechecked
    def remove_by_name(self, name: str):
        if name not in self._name_to_album:
            raise RuntimeError(
                f"Cannot remove: album with name '{name}' does not exist in AlbumNameMap."
            )
        del self._name_to_album[name]

    @typechecked
    def remove_by_name_or_id(self, album: AlbumResponseWrapper):
        # Try to remove by current name
        name = album.get_album_name()
        if name in self._name_to_album:
            del self._name_to_album[name]
            return
        # Fallback: try to remove by any name associated with the same UUID
        album_uuid = album.get_album_uuid()
        for n, a in list(self._name_to_album.items()):
            if a.get_album_uuid() == album_uuid:
                del self._name_to_album[n]
                return
        raise RuntimeError(
            f"Cannot remove: album with name '{name}' and uuid '{album_uuid}' does not exist in AlbumNameMap."
        )
