from typing import Iterable, Iterator

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


class AlbumList:
    def __init__(self, albums: Iterable[AlbumResponseWrapper] = ()):  # default empty
        self._albums = list(albums)

    def append(self, album: AlbumResponseWrapper):
        self._albums.append(album)

    def remove(self, album: AlbumResponseWrapper):
        self._albums.remove(album)

    def __iter__(self) -> Iterator[AlbumResponseWrapper]:
        return iter(self._albums)

    def __len__(self) -> int:
        return len(self._albums)

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album in self._albums

    def to_list(self) -> list[AlbumResponseWrapper]:
        return list(self._albums)

    def clear(self):
        self._albums.clear()

    def __bool__(self):
        return bool(self._albums)

    def __getitem__(self, idx):
        return self._albums[idx]

    def __repr__(self):
        return f"AlbumList({self._albums!r})"

    # Decorator removed, 'typecheck' does not exist
    @typechecked
    def remove_album(self, album: AlbumResponseWrapper):
        """Remove all occurrences of album from the list."""
        self._albums = [a for a in self._albums if a != album]
