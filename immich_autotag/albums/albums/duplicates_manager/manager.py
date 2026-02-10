from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

import attrs
from typeguard import typechecked

from immich_autotag.albums.album_and_modification import AlbumAndModification
from immich_autotag.albums.duplicates.collect_duplicate import collect_duplicate
from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReports,
)
from immich_autotag.albums.duplicates.merge_duplicate_albums import (
    merge_duplicate_albums,
)
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.report.modification_report import ModificationReport


@attrs.define(auto_attribs=True, slots=True)
class DuplicateAlbumManager:
    """
    Encapsulates all logic for managing duplicate albums:
    - Duplicate detection
    - Combination and merging
    - Reporting and storage
    """

    collection: "AlbumCollectionWrapper"
    collected_duplicates: "DuplicateAlbumReports" = attrs.Factory(DuplicateAlbumReports)

    from immich_autotag.albums.album_and_modification import AlbumAndModification
    from immich_autotag.report.modification_entries_list import ModificationEntriesList

    @typechecked
    def _handle_duplicate_album_conflict(
        self,
        incoming_album: "AlbumResponseWrapper",
        existing_album: "AlbumResponseWrapper",
        context: str = "ensure_unique",
    ) -> AlbumAndModification:
        # Import local para evitar ciclo

        name_existing = existing_album.get_album_name()
        name_incoming = incoming_album.get_album_name()

        # If both albums have the same UUID, treat as no-op modification
        if existing_album.get_album_uuid() == incoming_album.get_album_uuid():
            best = existing_album.get_best_cache_entry(incoming_album)
            return AlbumAndModification(
                album=best,
                modifications=ModificationEntriesList(),
            )

        if name_existing != name_incoming:
            raise ValueError(
                f"Integrity check failed in handle_duplicate_album_conflict: "
                f"album names differ ('{name_existing}' vs '{name_incoming}'). "
                f"Context: {context}"
            )
        from immich_autotag.config.internal_config import MERGE_DUPLICATE_ALBUMS_ENABLED

        if MERGE_DUPLICATE_ALBUMS_ENABLED:
            client = self.collection.get_client()
            tag_mod_report = self.collection.get_modification_report()
            mods = merge_duplicate_albums(
                target_album=existing_album,
                collection=self.collection,
                duplicate_album=incoming_album,
                client=client,
                tag_mod_report=tag_mod_report,
            )
            albums = mods.get_albums()
            if len(albums) != 1 or existing_album not in albums:
                raise ValueError(
                    f"ModificationEntriesList integrity error: expected only album '{existing_album.get_album_name()}', got {albums}"
                )
            return AlbumAndModification(
                album=existing_album,
                modifications=mods,
            )
        else:
            from immich_autotag.config.dev_mode import is_development_mode

            if is_development_mode():
                raise RuntimeError(
                    f"Duplicate album name detected when adding album: "
                    f"{existing_album.get_album_name()!r}"
                )
        collect_duplicate(
            self.collected_duplicates, existing_album, incoming_album, context
        )
        return AlbumAndModification(
            album=existing_album,
            modifications=ModificationEntriesList(),
        )

    @typechecked
    def _handle_non_temporary_duplicate(
        self,
        *,
        existing: "AlbumResponseWrapper",
        incoming_album: "AlbumResponseWrapper",
        tag_mod_report: ModificationReport,
        name: str,
    ) -> None:
        from immich_autotag.config.internal_config import MERGE_DUPLICATE_ALBUMS_ENABLED

        if MERGE_DUPLICATE_ALBUMS_ENABLED:
            self._handle_duplicate_album_conflict(
                incoming_album=incoming_album,
                existing_album=existing,
                context="duplicate_on_load",
            )
            return
        from immich_autotag.config.dev_mode import is_development_mode

        if is_development_mode():
            raise RuntimeError(
                f"Duplicate album name detected when adding album: {name!r}"
            )
            return
        from immich_autotag.albums.duplicates.duplicate_album_reports import (
            DuplicateAlbumReport,
        )

        self.collected_duplicates.append(
            DuplicateAlbumReport(
                album_name=name,
                existing_album=existing,
                incoming_album=incoming_album,
                note="duplicate skipped during initial load",
            )
        )
        from immich_autotag.report.modification_kind import ModificationKind

        tag_mod_report.add_error_modification(
            kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
            error_message=f"duplicate album name encountered: {name}",
            error_category="DUPLICATE_ALBUM",
            extra={
                "existing_id": existing.get_album_uuid(),
                "incoming_id": incoming_album.get_album_uuid(),
            },
        )
        return

    def handle_non_temporary_duplicate(
        self,
        *,
        existing: "AlbumResponseWrapper",
        incoming_album: "AlbumResponseWrapper",
        tag_mod_report: ModificationReport,
        name: str,
    ) -> None:
        return self._handle_non_temporary_duplicate(
            existing=existing,
            incoming_album=incoming_album,
            tag_mod_report=tag_mod_report,
            name=name,
        )

    @typechecked
    def is_duplicated(self, wrapper: "AlbumResponseWrapper") -> bool:
        name = wrapper.get_album_name()
        names = self.collection.find_all_albums_with_name(name)
        return len(list(names)) > 1

    @typechecked
    def combine_duplicate_albums(
        self, albums: list["AlbumResponseWrapper"], context: str
    ) -> AlbumAndModification:
        if not albums:
            raise ValueError(
                f"No albums provided to combine_duplicate_albums (context: {context})"
            )
        if len(albums) < 2:
            album = albums[0]
            if not album.is_duplicate_album():
                raise RuntimeError(
                    f"Refusing to combine album '{album.get_album_name()}' "
                    f"(id={album.get_album_uuid()}): not a duplicate album."
                )
            return AlbumAndModification(
                album=album,
                modifications=ModificationEntriesList(),
            )
        survivors = [
            AlbumAndModification(album=a, modifications=ModificationEntriesList())
            for a in albums
        ]
        while len(survivors) > 1:
            existing = survivors[0]
            incoming = survivors[1]
            result = self._handle_duplicate_album_conflict(
                incoming_album=incoming.get_album(),
                existing_album=existing.get_album(),
                context=context,
            )
            combined_modifications = ModificationEntriesList.combine_optional(
                existing.get_modifications(), result.get_modifications()
            )
            # Ensure combined_modifications is always a ModificationEntriesList, never None
            if combined_modifications is None:
                combined_modifications = ModificationEntriesList()
            survivors = [
                AlbumAndModification(
                    album=result.get_album(), modifications=combined_modifications
                )
            ] + survivors[2:]
        return survivors[0]
