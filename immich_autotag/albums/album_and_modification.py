from __future__ import annotations

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.report.modification_entry import ModificationEntry


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumAndModification:


    _album: AlbumResponseWrapper
    _modifications: ModificationEntriesList

    @typechecked
    def get_album(self) -> AlbumResponseWrapper:
        return self._album

    @typechecked
    def get_modifications(self) -> ModificationEntriesList:
        return self._modifications

    @staticmethod
    @typechecked
    def combine_optional(
        first: AlbumAndModification | None,
        second: AlbumAndModification | None,
    ) -> AlbumAndModification | None:
        """
        Combine two AlbumAndModification instances, aggregating modifications and keeping the album from the first.
        Returns None if both are None.
        """
        if first is None and second is None:
            return None
        if first is None:
            return second
        if second is None:
            return first
        combined_mods = ModificationEntriesList.combine_optional(
            first.get_modifications(), second.get_modifications()
        )
        if combined_mods is None:
            combined_mods = ModificationEntriesList()
        return AlbumAndModification(first.get_album(), combined_mods)

    @staticmethod
    @typechecked
    def from_album_and_modifications(
        album: AlbumResponseWrapper, modifications: ModificationEntriesList
    ) -> "AlbumAndModification":
        """
        Static constructor for AlbumAndModification.
        Use this to avoid issues with attrs and positional/keyword arguments.
        """
        return AlbumAndModification(album, modifications)

    @staticmethod
    @typechecked
    def from_album_and_entry(
        album: AlbumResponseWrapper,
        entry: ModificationEntry | None,
    ) -> "AlbumAndModification":
        """
        Static constructor for AlbumAndModification from a single ModificationEntry or None.
        If entry is None, returns AlbumAndModification with empty modifications.
        """
        from immich_autotag.report.modification_entry import ModificationEntry
        if entry is None:
            return AlbumAndModification(album, ModificationEntriesList())
        assert isinstance(entry, ModificationEntry), "entry must be a ModificationEntry or None"
        return AlbumAndModification(album, ModificationEntriesList([entry]))


    @staticmethod
    @typechecked
    def from_album(album: AlbumResponseWrapper) -> "AlbumAndModification":
        """
        Static constructor for AlbumAndModification with no modifications.
        """
        return AlbumAndModification(album, ModificationEntriesList())