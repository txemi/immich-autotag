from typing import Iterator

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.types.uuid_wrappers import AlbumUUID


@attrs.define(auto_attribs=True, slots=True)
class AlbumList:

    _albums: list[AlbumResponseWrapper] = attrs.field(
        factory=list,
        repr=lambda value: f"size={len(value)}",
    )

    @typechecked
    def get_by_uuid(self, uuid: AlbumUUID) -> AlbumResponseWrapper | None:
        """
        Returns the album with the given UUID (UUID or AlbumUUID), or None if not found.
        """
        # Always compare as UUID
        uuid_val = uuid.to_uuid()

        for album in self._albums:
            if album.get_album_uuid() == uuid_val:
                return album
        return None

    @typechecked
    def append(self, album: AlbumResponseWrapper):
        if album in self._albums:
            raise ValueError("Album already in AlbumList (no uuid)")
        album_id = album.get_album_uuid()
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

    def get_album_names(self) -> list[str]:
        """
        Returns a list of album names for all albums in the list.
        """
        return [album.get_album_name() for album in self._albums]

    def is_empty(self) -> bool:
        """
        Returns True if the album list is empty.
        """
        return len(self._albums) == 0

    def deduplicate(self) -> "AlbumList":
        """
        Return a new AlbumList containing unique albums by UUID.
        """
        seen_ids = set()
        unique_albums = []
        for album in self._albums:
            album_id = str(album.get_album_uuid())
            if album_id not in seen_ids:
                seen_ids.add(album_id)
                unique_albums.append(album)
        return AlbumList(unique_albums)

    def uuids_set(self) -> set:
        """
        Return a set of UUIDs for all albums in the list.
        """
        return set(str(album.get_album_uuid()) for album in self._albums)

    def equals(self, other: "AlbumList") -> bool:
        """
        Return True if both AlbumList instances contain the same albums by UUID (order-independent).
        """
        return self.uuids_set() == other.uuids_set()

    def difference(self, other: "AlbumList") -> "AlbumList":
        """
        Return an AlbumList containing albums present in self but not in other (by UUID).
        """
        other_uuids = other.uuids_set()
        diff_albums = [
            album
            for album in self._albums
            if str(album.get_album_uuid()) not in other_uuids
        ]
        return AlbumList(diff_albums)

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
