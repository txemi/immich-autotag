import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.albums.duplicates.collect_duplicate import collect_duplicate
from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReports,
)
from immich_autotag.albums.duplicates.merge_duplicate_albums import (
    merge_duplicate_albums,
)
from immich_autotag.report.modification_report import ModificationReport


@attrs.define(auto_attribs=True, slots=True)
class DuplicateAlbumManager:
    """
    Encapsulates all logic for managing duplicate albums:
    - Duplicate detection
    - Combination and merging
    - Reporting and storage
    """

    collection: AlbumCollectionWrapper
    collected_duplicates: DuplicateAlbumReports = attrs.Factory(DuplicateAlbumReports)

    @typechecked
    def _handle_duplicate_album_conflict(
        self,
        incoming_album: AlbumResponseWrapper,
        existing_album: AlbumResponseWrapper,
        context: str = "ensure_unique",
    ) -> AlbumResponseWrapper:
        name_existing = existing_album.get_album_name()
        name_incoming = incoming_album.get_album_name()
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
            return merge_duplicate_albums(
                target_album=existing_album,
                collection=self.collection,
                duplicate_album=incoming_album,
                client=client,
                tag_mod_report=tag_mod_report,
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
        return existing_album

    @typechecked
    def _handle_non_temporary_duplicate(
        self,
        *,
        existing: AlbumResponseWrapper,
        incoming_album: AlbumResponseWrapper,
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
        existing: AlbumResponseWrapper,
        incoming_album: AlbumResponseWrapper,
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
    def is_duplicated(self, wrapper: AlbumResponseWrapper) -> bool:
        name = wrapper.get_album_name()
        names = self.collection.find_all_albums_with_name(name)
        return len(list(names)) > 1

    @typechecked
    def combine_duplicate_albums(
        self, albums: list[AlbumResponseWrapper], context: str
    ) -> AlbumResponseWrapper:
        if not albums:
            raise ValueError(
                f"No albums provided to combine_duplicate_albums (context: {context})"
            )
        for album in albums:
            if not album.is_duplicate_album():
                raise RuntimeError(
                    f"Refusing to combine album '{album.get_album_name()}' "
                    f"(id={album.get_album_uuid()}): not a duplicate album."
                )
        survivors = list(albums)
        while len(survivors) > 1:
            existing_album = survivors[0]
            incoming_album = survivors[1]
            surviving_album = self._handle_duplicate_album_conflict(
                incoming_album=incoming_album,
                existing_album=existing_album,
                context=context,
            )
            survivors = [surviving_album] + survivors[2:]
        return survivors[0]
