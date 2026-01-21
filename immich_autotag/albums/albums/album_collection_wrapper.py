from __future__ import annotations

from typing import Iterable
from uuid import UUID
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_autotag.context.immich_context import ImmichContext

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_list import AlbumList
from immich_autotag.albums.albums.asset_to_albums_map import AssetToAlbumsMap
from immich_autotag.albums.albums.unavailable_albums import UnavailableAlbums
from immich_autotag.albums.duplicates.collect_duplicate import collect_duplicate
from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReports,
)
from immich_autotag.albums.duplicates.merge_duplicate_albums import (
    merge_duplicate_albums,
)
from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album

# Import for type checking and runtime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient
from immich_autotag.utils.decorators import conditional_typechecked

# Singleton instance storage


_album_collection_singleton: AlbumCollectionWrapper | None = None



@attrs.define(auto_attribs=True, slots=True)
class AlbumCollectionWrapper:


    _albums: AlbumList = attrs.field(validator=attrs.validators.instance_of(AlbumList))
    _asset_to_albums_map: AssetToAlbumsMap = attrs.field(
        init=False,
        factory=AssetToAlbumsMap,
        validator=attrs.validators.instance_of(AssetToAlbumsMap),
    )
    _unavailable: UnavailableAlbums = attrs.field(
        init=False, factory=UnavailableAlbums, repr=False
    )
    # Collected duplicate album reports (instance-level). Used when running
    # in non-development modes to accumulate duplicates for operator review.
    _collected_duplicates: DuplicateAlbumReports = attrs.field(
        default=attrs.Factory(DuplicateAlbumReports), init=False, repr=False
    )
    @typechecked
    def find_first_album_with_name(self, album_name: str) -> AlbumResponseWrapper | None:
        """
        Returns the first album with the given name, or None if not found.
        Equivalent to next(self.find_all_albums_with_name(album_name), None).
        """
        for album in self.get_albums():
            if album.get_album_name() == album_name:
                return album
        return None
    @typechecked
    def set_albums(self, value: AlbumList) -> None:
        """
        Replaces the internal list of albums with the provided one.
        """
        self._albums = value

    @typechecked
    def get_albums(self) -> AlbumList:
        """
        Returns an iterator over the albums in the collection.
        Does not expose AlbumList directly.
        """
        return self._albums

    @typechecked
    def __attrs_post_init__(self) -> None:
        global _album_collection_singleton
        if _album_collection_singleton is not None:
            raise RuntimeError(
                "AlbumCollectionWrapper is a singleton: only one instance is allowed."
            )
        _album_collection_singleton = self
        # Asset map is built on demand, not during initialization

    @staticmethod
    @typechecked
    def get_client() -> ImmichClient:
        """Returns the current ImmichClient from the context singleton."""
        try:
            from immich_autotag.context.immich_context import ImmichContext

            return ImmichContext.get_default_client()
        except Exception as e:
            raise RuntimeError(f"Could not retrieve ImmichClient: {e}")

    @staticmethod
    @typechecked
    def get_modification_report() -> ModificationReport:
        """Returns the current ModificationReport singleton."""
        try:
            from immich_autotag.report.modification_report import ModificationReport

            return ModificationReport.get_instance()
        except Exception as e:
            raise RuntimeError(f"Could not retrieve ModificationReport: {e}")

    @typechecked
    def _rebuild_asset_to_albums_map(self) -> None:
        """Rebuilds the asset-to-albums map from scratch."""

        self._asset_to_albums_map = self._asset_to_albums_map_build()

    @typechecked
    def _add_album_to_map(self, album_wrapper: AlbumResponseWrapper) -> None:
        for asset_id in album_wrapper.get_asset_ids():
            if asset_id not in self._asset_to_albums_map:
                self._asset_to_albums_map[asset_id] = AlbumList()
            self._asset_to_albums_map[asset_id].append(album_wrapper)

    @typechecked
    def _remove_album_from_map(self, album_wrapper: AlbumResponseWrapper) -> None:
        for asset_id in album_wrapper.get_asset_ids():
            if asset_id in self._asset_to_albums_map:
                album_list = self._asset_to_albums_map[asset_id]
                album_list.remove_album(album_wrapper)
                if not album_list:
                    del self._asset_to_albums_map[asset_id]

    @classmethod
    def get_instance(cls) -> "AlbumCollectionWrapper":
        global _album_collection_singleton
        if _album_collection_singleton is None:
            raise RuntimeError(
                "AlbumCollectionWrapper singleton has not been initialized yet."
            )
        return _album_collection_singleton

    @typechecked
    def _remove_album_from_local_collection(
        self, album_wrapper: AlbumResponseWrapper
    ) -> bool:
        """
        Removes an album from the internal collection and updates the map incrementally. Returns True if removed, False if not present.
        """
        if album_wrapper in self._albums:
            self.set_albums(AlbumList([a for a in self._albums if a != album_wrapper]))
            self._remove_album_from_map(album_wrapper)
            return True
        return False

    @typechecked
    def remove_album_local(self, album_wrapper: AlbumResponseWrapper) -> bool:
        """
        Removes an album from the internal collection only (no API call).
        Returns True if removed, False if not present.
        Also invalidates the asset-to-albums map cache.
        """
        removed = self._remove_album_from_local_collection(album_wrapper)
        if removed:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(
                f"[ALBUM REMOVAL] Album {album_wrapper.get_album_id()} ('{album_wrapper.get_album_name()}') removed from collection (local, not_found cleanup).",
                level=LogLevel.FOCUS,
            )
        return removed

    @typechecked
    def notify_album_marked_unavailable(
        self, album_wrapper: AlbumResponseWrapper
    ) -> None:
        """Notify collection that an album was marked unavailable.

        This updates internal counters and triggers a global policy evaluation.
        """
        try:
            album_id = album_wrapper.get_album_id()
        except Exception:
            album_id = None
        if album_id is None:
            return
        # Use wrapper identity (by album id) for membership; avoid double-counting
        added = self._unavailable.add(album_wrapper)
        if not added:
            return

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            f"Album {album_id} marked unavailable (total_unavailable={self._unavailable.count}).",
            level=LogLevel.FOCUS,
        )

        # Evaluate global policy after this change
        try:
            self._evaluate_global_policy()
        except Exception:
            # Bubble up in development mode, otherwise swallow to continue processing
            raise

    @typechecked
    def _handle_duplicate_album_conflict(
        self,
        incoming_album: AlbumResponseWrapper,
        existing_album: AlbumResponseWrapper,
        context: str = "ensure_unique",
    ) -> AlbumResponseWrapper:
        """
        Centralizes duplicate album handling logic:
        - Applies merge if the flag is active and returns the resulting album
        - Fails fast in development mode
        - Collects the duplicate in other modes
        Performs an integrity check: both albums must have the same name.
        """
        # Integrity check: both albums must have the same name
        name_existing = existing_album.get_album_name()
        name_incoming = incoming_album.get_album_name()
        if name_existing != name_incoming:
            raise ValueError(
                f"Integrity check failed in _handle_duplicate_album_conflict: album names differ ('{name_existing}' vs '{name_incoming}'). Context: {context}"
            )
        from immich_autotag.config._internal_types import ErrorHandlingMode
        from immich_autotag.config.internal_config import (
            DEFAULT_ERROR_MODE,
            MERGE_DUPLICATE_ALBUMS_ENABLED,
        )

        if MERGE_DUPLICATE_ALBUMS_ENABLED:
            client = AlbumCollectionWrapper.get_client()
            tag_mod_report = AlbumCollectionWrapper.get_modification_report()
            return merge_duplicate_albums(
                target_album=existing_album,
                collection=self,
                duplicate_album=incoming_album,
                client=client,
                tag_mod_report=tag_mod_report,
            )
        elif DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
            raise RuntimeError(
                f"Duplicate album name detected when adding album: {existing_album.get_album_name()!r}"
            )
        collect_duplicate(
            self._collected_duplicates, existing_album, incoming_album, context
        )
        return existing_album



    @typechecked
    def write_unavailable_summary(self) -> None:
        """Write a small JSON summary of unavailable albums for operator inspection.

        Behavior:
        - The function returns `None` (it's a side-effecting writer).
        - The helper `_unavailable_sort_key` returns a string used for sorting.
        - If an unavailable album lacks an ID or retrieving the name/id raises,
          this is considered a programming/data error and the function will
          raise so the problem is surfaced (fail-fast).
        - Only filesystem/write errors when persisting the summary are
          swallowed in PRODUCTION mode; in DEVELOPMENT they will propagate.
        """
        import json

        from immich_autotag.config._internal_types import ErrorHandlingMode

        # Import error-mode config so we can decide whether to swallow IO errors
        # Fail-fast: configuration symbols must exist; let ImportError propagate.
        from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
        from immich_autotag.utils.run_output_dir import get_run_output_dir

        summary_items = []

        def _unavailable_sort_key(w: AlbumResponseWrapper) -> str:
            # Intent: return a stable string key for sorting. If the album has
            # no id (None) we treat that as an error and raise so it is fixed.
            album_id = w.get_album_id()
            if album_id is None:
                raise RuntimeError(
                    f"Album missing id while writing unavailable summary: {w!r}"
                )
            return str(album_id)

        # Build summary; allow failures to surface (fail-fast on bad album data)
        for wrapper in self._unavailable.sorted(_unavailable_sort_key):
            # These calls should not silently fail; surface issues to operator/dev.
            album_id = wrapper.get_album_id()
            if album_id is None:
                raise RuntimeError(
                    f"Album missing id while building summary: {wrapper!r}"
                )
            name = wrapper.get_album_name()
            summary_items.append({"id": album_id, "name": name})

        out_dir = get_run_output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "albums_unavailable_summary.json"

        try:
            with out_file.open("w", encoding="utf-8") as fh:
                json.dump(
                    {"count": len(summary_items), "albums": summary_items}, fh, indent=2
                )
        except Exception:
            # In DEVELOPMENT we want to see IO problems; in PRODUCTION we
            # swallow write errors to avoid crashing the run.
            if DEFAULT_ERROR_MODE is not None and ErrorHandlingMode is not None:
                if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                    raise
                # else: swallow in production
            else:
                # If we couldn't determine error mode, be conservative and raise
                raise

    @typechecked
    def _evaluate_global_policy(self) -> None:
        """Evaluate global unavailable-albums policy and act according to config.

        In DEVELOPMENT mode this may raise to fail-fast. In PRODUCTION it logs and
        records a summary event.
        """
        try:
            from immich_autotag.config._internal_types import ErrorHandlingMode
            from immich_autotag.config.internal_config import (
                DEFAULT_ERROR_MODE,
                GLOBAL_UNAVAILABLE_THRESHOLD,
            )
            from immich_autotag.report.modification_report import ModificationReport
            from immich_autotag.tags.modification_kind import ModificationKind
        except Exception:
            return

        try:
            threshold = int(GLOBAL_UNAVAILABLE_THRESHOLD)
        except Exception:
            return

        if self._unavailable.count >= threshold:
            # In development: fail fast to surface systemic problems
            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise RuntimeError(
                    f"Too many albums marked unavailable during run: {self._unavailable.count} >= {threshold}. Failing fast (DEVELOPMENT mode)."
                )

            # In production: record a summary event and continue
            try:
                tag_mod_report = ModificationReport.get_instance()
                tag_mod_report.add_error_modification(
                    kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
                    error_message=f"global unavailable threshold exceeded: {self._unavailable.count} >= {threshold}",
                    error_category="GLOBAL_THRESHOLD",
                    extra={
                        "unavailable_count": self._unavailable.count,
                        "threshold": threshold,
                    },
                )
                # Write a small summary file for operator inspection
                try:
                    self.write_unavailable_summary()
                except Exception:
                    pass
            except Exception:
                pass

    @typechecked
    def _asset_to_albums_map_build(self) -> AssetToAlbumsMap:
        """Pre-computed map: asset_id -> AlbumList of AlbumResponseWrapper objects (O(1) lookup).

        Before building the map, forces the loading of asset_ids in all albums (lazy loading).
        """
        asset_map = AssetToAlbumsMap()
        assert (
            len(self._albums) > 0
        ), "AlbumCollectionWrapper must have at least one album to build asset map."
        from immich_autotag.context.immich_context import ImmichContext

        client = ImmichContext.get_default_client()
        for album_wrapper in self._albums:
            # Ensures the album is in full mode (assets loaded)
            # album_wrapper.ensure_full()
            if album_wrapper.is_empty():
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(
                    f"Album '{album_wrapper.get_album_name()}' has no assets after forced reload.",
                    level=LogLevel.WARNING,
                )
                # album_wrapper.reload_from_api(client)
                if album_wrapper.get_asset_ids():
                    album_url = album_wrapper.get_immich_album_url().geturl()
                    raise RuntimeError(
                        f"[DEBUG] Anomalous behavior: Album '{album_wrapper.get_album_name()}' (URL: {album_url}) had empty asset_ids after initial load, but after a redundant reload it now has assets. "
                        "This suggests a possible synchronization or lazy loading bug. Please review the album loading logic."
                    )
                if is_temporary_album(album_wrapper.get_album_name()):
                    from immich_autotag.logging.levels import LogLevel
                    from immich_autotag.logging.utils import log

                    log(
                        f"Temporary album '{album_wrapper.get_album_name()}' marked for removal after map build.",
                        level=LogLevel.WARNING,
                    )
            else:
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(
                    f"Album '{album_wrapper.get_album_name()}' reloaded with {len(album_wrapper.get_asset_ids())} assets.",
                    level=LogLevel.INFO,
                )
            for asset_id in album_wrapper.get_asset_ids():
                if asset_id not in asset_map:
                    asset_map[asset_id] = AlbumList()
                asset_map[asset_id].append(album_wrapper)
        albums_to_remove = self._detect_empty_temporary_albums()

        # Removes empty temporary albums detected after building the map
        self._remove_empty_temporary_albums(albums_to_remove, client)

        return asset_map

    @typechecked
    def _remove_empty_temporary_albums(
        self, albums_to_remove: list[AlbumResponseWrapper], client: ImmichClient
    ):
        """
        Removes empty temporary albums detected after building the map.
        Raises an exception if any of them is not temporary (integrity).
        """
        if not albums_to_remove:
            return
        # Integrity check: all must be temporary
        for album_wrapper in albums_to_remove:
            if not is_temporary_album(album_wrapper.get_album_name()):
                raise RuntimeError(
                    f"Integrity check failed: album '{album_wrapper.get_album_name()}' (id={album_wrapper.get_album_id()}) is not temporary but was passed to _remove_empty_temporary_albums."
                )

        tag_mod_report = ModificationReport.get_instance()
        for album_wrapper in albums_to_remove:
            try:
                self.delete_album(
                    wrapper=album_wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                    reason="Removed automatically after map build because it was empty and temporary",
                )
                self._remove_album_from_local_collection(album_wrapper)
            except Exception as e:
                album_name = album_wrapper.get_album_name()
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(
                    f"Failed to remove temporary album '{album_name}': {e}",
                    level=LogLevel.ERROR,
                )
                raise

    @typechecked
    def _detect_empty_temporary_albums(self) -> list[AlbumResponseWrapper]:
        """
        Returns a list of empty temporary albums to be removed after building the map.
        """
        albums_to_remove: list[AlbumResponseWrapper] = []
        for album_wrapper in self.get_albums():
            if album_wrapper.is_empty() and is_temporary_album(
                album_wrapper.get_album_name()
            ):
                albums_to_remove.append(album_wrapper)
        return albums_to_remove

    @staticmethod
    @typechecked
    def delete_album(
        *,
        wrapper: AlbumResponseWrapper,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
        reason: str = "Album deleted",
    ) -> bool:
        """
        Deletes an album on the server and records the action, whether temporary or not.
        Returns True if deleted successfully or if it no longer exists.
        """
        from uuid import UUID

        from immich_client.api.albums.delete_album import (
            sync_detailed as delete_album_sync,
        )

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        # Safety check: only allow deletion of temporary or duplicate albums
        if not wrapper.is_temporary_album():
            # Only allow deletion if it is a duplicate
            if not wrapper.is_duplicate_album():
                raise RuntimeError(
                    f"Refusing to delete album '{wrapper.get_album_name()}' (id={wrapper.get_album_id()}): not a temporary or duplicate album."
                )
        try:
            delete_album_sync(id=UUID(wrapper.get_album_id()), client=client)
        except Exception as exc:
            msg = str(exc)
            # Try to give a more specific reason if possible
            code_checked = False
            try:
                code = (
                    exc.response.status_code
                )  # Explicit access, will raise if not present
                if code == 404:
                    err_reason = "Album not found (already deleted)"
                    code_checked = True
                elif code == 400:
                    err_reason = "Album not empty or bad request"
                    code_checked = True
                elif code == 403:
                    err_reason = "Permission denied"
                    code_checked = True
                else:
                    err_reason = f"HTTP {code}"
                    code_checked = True
            except AttributeError:
                pass
            if not code_checked:
                if "not found" in msg.lower():
                    err_reason = "Album not found (already deleted)"
                elif "not empty" in msg.lower():
                    err_reason = "Album not empty"
                elif "permission" in msg.lower() or "forbidden" in msg.lower():
                    err_reason = "Permission denied"
                else:
                    err_reason = "Unknown error"
            log(
                f"Failed to delete album '{wrapper.get_album_name()}' (id={wrapper.get_album_id()}). Reason: {err_reason}. Exception: {msg}",
                level=LogLevel.WARNING,
            )
            self.remove_album_local_public(wrapper)
            from immich_autotag.tags.modification_kind import ModificationKind
            tag_mod_report.add_album_modification(
                kind=ModificationKind.DELETE_ALBUM,
                album=wrapper,
                old_value=wrapper.get_album_name(),
                extra={"reason": f"{reason} (FAILED: {err_reason})"},
            )
            return True
        self.remove_album_local_public(wrapper)
        from immich_autotag.tags.modification_kind import ModificationKind
        tag_mod_report.add_album_modification(
            kind=ModificationKind.DELETE_ALBUM,
            album=wrapper,
            old_value=wrapper.get_album_name(),
            extra={"reason": f"{reason} (FAILED: {err_reason})"},
        )
        return True
    def remove_album_local_public(self, album_wrapper: AlbumResponseWrapper) -> bool:
        """
        Public wrapper for _remove_album_from_local_collection.
        """
        return self._remove_album_from_local_collection(album_wrapper)

    @typechecked
    def _handle_non_temporary_duplicate(
        self,
        *,
        existing: AlbumResponseWrapper,
        incoming_album: AlbumResponseWrapper,
        tag_mod_report: ModificationReport,
        duplicates_collected: list[dict[str, object]],
        name: str,
    ) -> None:
        """
        Handles the case of a non-temporary duplicate: error in development, collection in other modes.
        """

        from immich_autotag.config._internal_types import ErrorHandlingMode
        from immich_autotag.config.internal_config import (
            DEFAULT_ERROR_MODE,
            MERGE_DUPLICATE_ALBUMS_ENABLED,
        )

        if MERGE_DUPLICATE_ALBUMS_ENABLED:
            # Centralizes handling en el método unificado
            self._handle_duplicate_album_conflict(
                incoming_album=incoming_album,
                existing_album=existing,
                context="duplicate_on_load",
            )
        elif DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
            raise RuntimeError(
                f"Duplicate album name detected when adding album: {name!r}"
            )
        if duplicates_collected is not None:
            duplicates_collected.append(
                {
                    "name": name,
                    "existing_id": existing.get_album_id(),
                    "incoming_id": incoming_album.get_album_id(),
                    "note": "duplicate skipped durante carga inicial",
                }
            )
        if tag_mod_report is not None:
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report.add_error_modification(
                kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
                error_message=f"duplicate album name encountered: {name}",
                error_category="DUPLICATE_ALBUM",
                extra={
                    "existing_id": existing.get_album_id(),
                    "incoming_id": incoming_album.get_album_id(),
                },
            )
        return

    @typechecked
    def _try_append_wrapper_to_list(
        self,
        *,
        albums_list: list[AlbumResponseWrapper],
        wrapper: AlbumResponseWrapper,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
        duplicates_collected: "DuplicateAlbumReports",
    ) -> None:
        """Central helper: attempt to append a wrapper to an albums list with duplicate handling.

        If a duplicate name exists and it's a temporary album, attempt to delete the duplicate on
        the server (if `client` is provided) and skip adding. If it's a non-temporary duplicate,
        raise RuntimeError. This centralizes duplicate detection used during initial load and
        during runtime album creation.
        """
        name = wrapper.get_album_name()
        for existing in list(albums_list):
            try:
                if existing.get_album_name() == name:
                    # Temporary duplicate
                    if is_temporary_album(name) and client is not None:
                        if AlbumCollectionWrapper.delete_album(
                            wrapper=wrapper,
                            client=client,
                            tag_mod_report=tag_mod_report,
                            reason="Removed duplicate temporary album during add",
                        ):
                            return
                    # Non-temporary duplicate
                    self._handle_non_temporary_duplicate(
                        existing=existing,
                        incoming_album=wrapper,
                        tag_mod_report=tag_mod_report,
                        duplicates_collected=duplicates_collected,
                        name=name,
                    )
                    return
            except Exception:
                raise
        albums_list.append(wrapper)

    @typechecked
    def add_album_wrapper(
        self,
        wrapper: AlbumResponseWrapper,
        client: ImmichClient | None = None,
        tag_mod_report: ModificationReport | None = None,
    ) -> AlbumResponseWrapper:
        """Add a wrapper to this collection with centralized duplicate handling.

        If a duplicate exists and is temporary, attempt to delete it on the server
        and remove it locally before adding the provided wrapper. If duplicate is
        non-temporary, raise RuntimeError.
        """
        name = wrapper.get_album_name()
        existing = self.find_first_album_with_name(name)
        if existing is not None:
            raise RuntimeError(
                f"Cannot add album: an album with the name '{name}' already exists (id={existing.get_album_id()})."
            )
        # Append to collection and update maps
        self._albums.append(wrapper)
        # Optionally update asset-to-albums map or other structures here if needed
        return wrapper

    @conditional_typechecked
    def albums_for_asset(
        self, asset: AssetResponseWrapper
    ) -> Iterable[AlbumResponseWrapper]:
        """
        Returns an iterable of AlbumResponseWrapper objects for all albums the asset belongs to (O(1) lookup via map).
        """
        return self._asset_to_albums_map.get(asset.id, AlbumList())

    @conditional_typechecked
    def album_names_for_asset(self, asset: AssetResponseWrapper) -> list[str]:
        """Returns the names of the albums the asset belongs to.
        Use this only if you need names (e.g., for logging). Prefer albums_for_asset() for object access.
        """
        return [w.get_album_name() for w in self.albums_for_asset(asset)]

    @conditional_typechecked
    def albums_wrappers_for_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> Iterable[AlbumResponseWrapper]:
        """
        Returns an iterable of AlbumResponseWrapper objects for all albums the asset (wrapped or raw) belongs to.
        Accepts either AssetResponseWrapper or AssetResponseDto.
        """

        return self.albums_for_asset(asset_wrapper)

    # Método duplicado albums_with_name eliminado

    # remove_album deleted: use delete_album and _remove_album_from_local_collection
    @typechecked
    def find_all_albums_with_name(self, album_name: str):
        """
        Yields all AlbumResponseWrapper objects with the given name.
        Returns a generator (may yield none).
        """
        for album_wrapper in self.get_albums():
            if album_wrapper.get_album_name() == album_name:
                yield album_wrapper

    @typechecked
    def combine_duplicate_albums(
        self, albums: list[AlbumResponseWrapper], context: str
    ) -> AlbumResponseWrapper:
        """
        Combines a list of duplicate albums into one, applying a reduction algorithm:
        merges all albums two by two using the duplicate policy, always keeping the surviving album,
        until only one remains. The 'context' argument is mandatory and must indicate the origin or reason for the combination (for logs, exceptions, etc).
        Returns the resulting final album.
        """
        if not albums:
            raise ValueError(
                f"No albums provided to combine_duplicate_albums (context: {context})"
            )
        # Safety: Ensure all albums are true duplicates before merging
        for album in albums:
            if not album.is_duplicate_album():
                raise RuntimeError(
                    f"Refusing to combine album '{album.get_album_name()}' (id={album.get_album_id()}): not a duplicate album."
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
    @typechecked
    def _add_user_to_album(
        self,
        album: AlbumResponseDto,
        user_id: UUID,
        context: ImmichContext,
        tag_mod_report: ModificationReport,
    ) -> None:
        """
        Private helper to add a user as EDITOR to an album. Handles only user addition, error reporting, and event logging.
        """
        from immich_autotag.permissions.album_permission_executor import _add_members_to_album
        try:
            from immich_autotag.tags.modification_kind import ModificationKind
            _add_members_to_album(
                album_id=album.id,
                album_name=album.album_name,
                user_ids=[str(user_id)],
                access_level="editor",
                context=context,
            )
            tag_mod_report.add_album_modification(
                kind=ModificationKind.ADD_USER_TO_ALBUM,
                album=AlbumResponseWrapper.from_partial_dto(album),
                extra={"added_user": str(user_id)},
            )
        except Exception as e:
            raise RuntimeError(
                f"Error adding user {user_id} as EDITOR to album {album.id} ('{album.album_name}'): {e}"
            ) from e

    @typechecked
    def _create_album(
        self,
        album_name: str,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
    ) -> AlbumResponseDto:
        """
        Private helper to create an album via the API. Returns the album object. Handles creation, error reporting, and event logging.
        """
        from immich_client.api.albums import create_album
        from immich_client.models.create_album_dto import CreateAlbumDto
        from immich_autotag.tags.modification_kind import ModificationKind
        album = create_album.sync(client=client, body=CreateAlbumDto(album_name=album_name))
        if album is None:
            raise RuntimeError("Failed to create album: API returned None")
        tag_mod_report.add_album_modification(
            kind=ModificationKind.CREATE_ALBUM,
            album=AlbumResponseWrapper.from_partial_dto(album),
            extra={"created": True},
        )
        return album

    @conditional_typechecked
    def create_or_get_album_with_user(
        self,
        album_name: str,
        client: ImmichClient,
        tag_mod_report: ModificationReport = None,
    ) -> "AlbumResponseWrapper":
        """
        Searches for an album by name. If one exists, returns it. If there is more than one, handles duplicates according to the policy (merge, delete temporary, error, etc).
        If it doesn't exist (or after cleaning duplicates it no longer exists), creates it and assigns the current user as EDITOR.
        """
        # Search for all albums with that name
        albums_found = list(self.find_all_albums_with_name(album_name))
        if len(albums_found) == 1:
            return albums_found[0]
        elif len(albums_found) > 1:
            result = self.combine_duplicate_albums(
                albums_found, context="duplicate_on_create"
            )
            # Lanzar excepción para desarrolladores tras la limpieza
            raise RuntimeError(
                f"Duplicate albums with name '{album_name}' were found and combined. This indicates a data integrity issue. Review the logs and investigate the cause."
            )

        # If it doesn't exist, create it and assign user
        from immich_autotag.context.immich_context import ImmichContext
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper
        if tag_mod_report is None:
            tag_mod_report = self.get_modification_report()

        album = self._create_album(album_name, client, tag_mod_report)

        # Centralized user access
        context = ImmichContext.get_instance()
        user_wrapper = UserResponseWrapper.from_context(context)
        user_id = user_wrapper.uuid
        wrapper = AlbumResponseWrapper.from_partial_dto(album)
        owner_id = wrapper.owner_uuid
        if user_id != owner_id:
            self._add_user_to_album(album, user_id, context, tag_mod_report)
        wrapper = AlbumResponseWrapper.from_partial_dto(album)
        wrapper = self.add_album_wrapper(
            wrapper, client=client, tag_mod_report=tag_mod_report
        )
        return wrapper

    @classmethod
    def from_client(cls, client: ImmichClient) -> "AlbumCollectionWrapper":
        """
        Fetches all album metadata from the API (without assets initially).

        Asset data is NOT loaded upfront to avoid N+1 API calls (which can timeout).
        Instead, assets are fetched lazily only when actually needed via AlbumResponseWrapper.

        This optimization reduces load time from hours (timeout) to seconds.
        Albums without assets will show (assets: unknown) until accessed.
        """
        from immich_client.api.albums import get_all_albums

        from immich_autotag.report.modification_report import ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        assert isinstance(tag_mod_report, ModificationReport)

        # Fetch only basic album metadata (without assets)
        albums = get_all_albums.sync(client=client)
        if albums is None:
            raise RuntimeError("Failed to fetch albums: API returned None")
        albums_wrapped: list[AlbumResponseWrapper] = []
        from immich_autotag.albums.duplicates.duplicate_album_reports import (
            DuplicateAlbumReports,
        )

        duplicates_collected = DuplicateAlbumReports()

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log("Albums:", level=LogLevel.INFO)
        # Create the empty collection
        collection = cls(albums=AlbumList([]))

        for album in albums:
            wrapper = AlbumResponseWrapper.from_partial_dto(album)
            try:
                collection._try_append_wrapper_to_list(
                    albums_list=albums_wrapped,
                    wrapper=wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                    duplicates_collected=duplicates_collected,
                )
            except RuntimeError:
                raise
            log(
                f"- {wrapper.get_album_name()} (assets: lazy-loaded)",
                level=LogLevel.INFO,
            )

        tag_mod_report.flush()
        if len(duplicates_collected) > 0:
            from immich_autotag.albums.duplicates.write_duplicates_summary import (
                write_duplicates_summary,
            )

            write_duplicates_summary(duplicates_collected)

        log(f"Total albums: {len(albums_wrapped)}", level=LogLevel.INFO)

        # Assign the final list to the collection and return it
        collection.set_albums(AlbumList(albums_wrapped))
        return collection
