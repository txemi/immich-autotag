from typing import Dict, Optional
import attrs
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

@attrs.define(auto_attribs=True, slots=True)
class AlbumNameMap:
    """
    Efficient mapping from album name (str) to AlbumResponseWrapper.
    Uses attrs for validation and robustness.
    """
    _name_to_album: Dict[str, AlbumResponseWrapper] = attrs.field(factory=dict)

    def add(self, album: AlbumResponseWrapper):
        self._name_to_album[album.get_album_name()] = album

    def remove(self, album: AlbumResponseWrapper):
        name = album.get_album_name()
        if name in self._name_to_album:
            del self._name_to_album[name]

    def get(self, name: str) -> Optional[AlbumResponseWrapper]:
        return self._name_to_album.get(name)

    def clear(self):
        self._name_to_album.clear()

    def values(self):
        return self._name_to_album.values()

    def __contains__(self, name: str) -> bool:
        return name in self._name_to_album

    def __len__(self):
        return len(self._name_to_album)
