import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class UnavailableAlbums:
    """
    Encapsulates tracking of unavailable albums and their count.
    """

    _albums: set[AlbumResponseWrapper] = attrs.field(
        factory=set, init=False, repr=False
    )

    def add(self, album: AlbumResponseWrapper) -> bool:
        if album in self._albums:
            return False
        self._albums.add(album)
        return True

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album in self._albums

    def __len__(self) -> int:
        return len(self._albums)

    @property
    def count(self) -> int:
        return len(self._albums)

    def sorted(self, key):
        return sorted(self._albums, key=key)

    def items(self):
        return self._albums
