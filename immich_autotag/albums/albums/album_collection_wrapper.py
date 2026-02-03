from __future__ import annotations

from enum import Enum, auto
from typing import Iterable
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_dual_map import AlbumDualMap
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
from immich_autotag.config.dev_mode import is_development_mode
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.users.user_response_wrapper import UserResponseWrapper
from immich_autotag.utils.decorators import conditional_typechecked
from immich_autotag.utils.perf.protocol import PerfPhaseTracker


class SyncState(Enum):
    NOT_STARTED = auto()
    SYNCING = auto()
    SYNCED = auto()


@attrs.define(auto_attribs=True, slots=True)
class AlbumCollectionWrapper:
    """
    Singleton class that manages the collection of all albums in the system.

    Responsibilities:
    - Maintains the master list of albums (AlbumList) and provides access to them.
    - Manages a map from asset_id to the list of albums containing each asset
        (AssetToAlbumsMap),
        enabling O(1) lookup of albums for a given asset.
    - Handles unavailable albums and duplicate album detection/merging.
    - Provides methods for adding, removing, and searching albums by name or UUID.
    - Coordinates album-related operations, including API synchronization and
        integrity checks.

    Only one instance of this class is allowed (singleton pattern).
    """

    _albums: AlbumDualMap = attrs.field(
        init=False,
        factory=AlbumDualMap,
        validator=attrs.validators.instance_of(AlbumDualMap),
    )
    _asset_to_albums_map: AssetToAlbumsMap | None = attrs.field(
        init=False,
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(AssetToAlbumsMap)
        ),
    )
    _unavailable: UnavailableAlbums = attrs.field(
        init=False, factory=UnavailableAlbums, repr=False
    )
    # Collected duplicate album reports (instance-level). Used when running
    # in non-development modes to accumulate duplicates for operator review.
    _collected_duplicates: DuplicateAlbumReports = attrs.field(
        default=attrs.Factory(DuplicateAlbumReports),
        init=False,
        repr=False,
    )

    # Enum to indicate sync state: NOT_STARTED, SYNCING, SYNCED
    _sync_state: SyncState = attrs.field(
        default=SyncState.NOT_STARTED,
        init=False,
        repr=False,
    )

    def _ensure_fully_loaded(self):
        """
        Ensures that all albums have been loaded (search performed).
        If not, triggers a full load.
        Prevents recursive resyncs by checking sync state.
        """
        if self._sync_state == SyncState.SYNCED:
            return self
        if self._sync_state == SyncState.SYNCING:
            # Prevent recursion: return empty or partial collection
            return self
        # Start sync
        self._sync_state = SyncState.SYNCING
        self.resync_from_api()
        return self

    def log_lazy_load_timing(self):
        import time

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            "[PROGRESS] [ALBUM-LAZY-LOAD] Starting lazy album loading",
            level=LogLevel.PROGRESS,
        )
        t0 = time.time()
        self._ensure_fully_loaded()
        t1 = time.time()
        log(
            f"[PROGRESS] [ALBUM-LAZY-LOAD] Finished lazy album loading. "
            f"Elapsed: {t1-t0:.2f} seconds.",
            level=LogLevel.PROGRESS,
        )

    def ensure_all_full(
        self, perf_phase_tracker: PerfPhaseTracker | None = None
    ) -> None:
        """
        Public method to force all albums in the collection to be fully loaded (DETAIL/full mode).
        Adds timing logs at PROGRESS level. Optionally tracks perf phase if tracker is provided.
        """
        import time

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log
        from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

        if isinstance(perf_phase_tracker, PerfPhaseTracker):
            perf_phase_tracker.mark(phase="full", event="start")
        log(
            "[PROGRESS] [ALBUM-FULL-LOAD] Starting full album load",
            level=LogLevel.PROGRESS,
        )
        t0 = time.time()
        albums = self.get_albums()
        total = len(albums)
        tracker = PerformanceTracker.from_total(total)
        for idx, album in enumerate(albums, 1):
            log(
                f"[ALBUM-FULL-LOAD][DEBUG] Loading album {idx}/{total}: '{album.get_album_name()}'",
                level=LogLevel.TRACE,
            )
            # Delegate the logic of when to log to the tracker
            if tracker.should_log_progress(idx):
                progress_msg = tracker.get_progress_description(idx)
                log(
                    f"[ALBUM-FULL-LOAD][PROGRESS] {progress_msg} | Album: '{album.get_album_name()}'",
                    level=LogLevel.PROGRESS,
                )
        t1 = time.time()
        log(
            f"[PROGRESS] [ALBUM-FULL-LOAD] Finished full album load. Elapsed: {t1-t0:.2f} seconds.",
            level=LogLevel.PROGRESS,
        )
        if isinstance(perf_phase_tracker, PerfPhaseTracker):
            perf_phase_tracker.mark(phase="full", event="end")

    @typechecked
    def __attrs_post_init__(self) -> None:
        # Asset map is built on demand, not during initialization
        pass

    @classmethod
    def get_instance(cls) -> "AlbumCollectionWrapper":
        raise NotImplementedError("Singleton pattern is not implemented.")

    @staticmethod
    @typechecked
    def get_client() -> ImmichClient:
        """Returns the current ImmichClient from the context singleton."""
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

        return ImmichClientWrapper.get_default_instance().get_client()

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
    def find_first_album_with_name(
        self, album_name: str
    ) -> AlbumResponseWrapper | None:
        """
        Returns the first non-deleted album with the given name, or None if not found.
        """
        return self._ensure_fully_loaded()._albums.get_by_name(album_name)

    @typechecked
    def get_albums(self) -> AlbumList:
        """
        Returns an AlbumList of only non-deleted albums.
        """
        all_allbums = self._ensure_fully_loaded()._albums
        return AlbumList([a for a in all_allbums.all() if not a.is_deleted()])

    @typechecked
    def _remove_album_from_local_collection(
        self, album_wrapper: AlbumResponseWrapper
    ) -> bool:
        """
        Logically deletes an album by marking it as deleted.
        Does not remove from the list.
        Returns True if marked. Raises if already deleted or not present.
        """

        if album_wrapper.is_deleted():
            raise RuntimeError(
                f"Album '{album_wrapper.get_album_name()}' "
                f"(id={album_wrapper.get_album_uuid()}) is already deleted."
            )
        album_wrapper.mark_deleted()
        if self._asset_to_albums_map is not None:
            self._asset_to_albums_map.remove_album_for_asset_ids(album_wrapper)
        self._albums.remove(album_wrapper)
        return True

    @typechecked
    def _remove_empty_temporary_albums(
        self, albums_to_remove: AlbumList, client: ImmichClient
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
                    f"Integrity check failed: album '{album_wrapper.get_album_name()}' "
                    f"(id={album_wrapper.get_album_uuid()}) is not temporary but was "
                    f"passed to _remove_empty_temporary_albums."
                )

        tag_mod_report = ModificationReport.get_instance()
        for album_wrapper in albums_to_remove:
            try:
                self.delete_album(
                    wrapper=album_wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                    reason=(
                        "Removed automatically after map build because it was empty "
                        "and temporary"
                    ),
                )
                # No need to call _remove_album_from_local_collection here
                # because delete_album already does it via remove_album_local_public
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
    def _detect_empty_temporary_albums(self) -> AlbumList:
        """
        Returns an AlbumList of empty temporary albums to be removed
        after building the map.
        """
        albums_to_remove = AlbumList()
        for album_wrapper in self.get_albums():
            if album_wrapper.is_empty() and is_temporary_album(
                album_wrapper.get_album_name()
            ):
                albums_to_remove.append(album_wrapper)
        return albums_to_remove

    @typechecked
    def _asset_to_albums_map_build(self) -> AssetToAlbumsMap:
        """Pre-computed map: asset_id -> AlbumList of AlbumResponseWrapper objects
        (O(1) lookup).

        Before building the map, forces the loading of asset_ids in all albums
        (lazy loading).
        """
        asset_map = AssetToAlbumsMap()
        assert (
            len(self._albums) > 0
        ), "AlbumCollectionWrapper must have at least one album to build asset map."

        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

        client = ImmichClientWrapper.get_default_instance().get_client()
        albums = self.get_albums()
        total = len(albums)
        tracker = None
        if total > 0:
            from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

            tracker = PerformanceTracker.from_total(total)
        for idx, album_wrapper in enumerate(albums, 1):
            # Ensures the album is in full mode (assets loaded)
            # album_wrapper.ensure_full()

            if album_wrapper.is_empty():
                log(
                    f"Album '{album_wrapper.get_album_name()}' "
                    f"has no assets after forced reload.",
                    level=LogLevel.WARNING,
                )
                # album_wrapper.reload_from_api(client)
                if album_wrapper.get_asset_uuids():
                    album_url = album_wrapper.get_immich_album_url().geturl()
                    raise RuntimeError(
                        f"[DEBUG] Anomalous behavior: Album "
                        f"'{album_wrapper.get_album_name()}' (URL: {album_url}) "
                        "had empty asset_ids after initial load, "
                        "but after a redundant reload it now has assets. "
                        "This suggests a possible synchronization or lazy loading bug. "
                        "Please review the album loading logic."
                    )
                if is_temporary_album(album_wrapper.get_album_name()):
                    log(
                        f"Temporary album '{album_wrapper.get_album_name()}' "
                        f"marked for removal after map build.",
                        level=LogLevel.WARNING,
                    )

            if tracker and tracker.should_log_progress(idx):
                progress_msg = tracker.get_progress_description(idx)
                log(
                    f"[ALBUM-MAP-BUILD][PROGRESS] {progress_msg}. Album "
                    f"'{album_wrapper.get_album_name()}' reloaded with "
                    f"{len(album_wrapper.get_asset_uuids())} assets.",
                    level=LogLevel.PROGRESS,
                )
            asset_map.add_album_for_asset_ids(album_wrapper)
        albums_to_remove = self._detect_empty_temporary_albums()

        # Removes empty temporary albums detected after building the map
        self._remove_empty_temporary_albums(albums_to_remove, client)

        return asset_map

    @typechecked
    def _rebuild_asset_to_albums_map(self) -> None:
        """Rebuilds the asset-to-albums map from scratch."""

        self._asset_to_albums_map = self._asset_to_albums_map_build()

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
                f"[ALBUM REMOVAL] Album {album_wrapper.get_album_uuid()} ('"
                f"{album_wrapper.get_album_name()}') removed from collection "
                f"(local, not_found cleanup).",
                level=LogLevel.FOCUS,
            )
        return removed

    # Method moved to UnavailableAlbums: use self._unavailable.write_summary() instead

    @typechecked
    def _evaluate_global_policy(self) -> None:
        """Evaluate global unavailable-albums policy and act according to config.

        In DEVELOPMENT mode this may raise to fail-fast. In PRODUCTION it logs and
        records a summary event.
        """

        from immich_autotag.config.internal_config import (
            GLOBAL_UNAVAILABLE_THRESHOLD,
        )
        from immich_autotag.report.modification_kind import ModificationKind
        from immich_autotag.report.modification_report import ModificationReport

        threshold = int(GLOBAL_UNAVAILABLE_THRESHOLD)

        if not self._unavailable.count >= threshold:
            return

        # In development: fail fast to surface systemic problems
        from immich_autotag.config.dev_mode import is_development_mode

        if is_development_mode():
            raise RuntimeError(
                f"Too many albums marked unavailable during run: "
                f"{self._unavailable.count} >= {threshold}. "
                f"Failing fast (DEVELOPMENT mode)."
            )

        # In production: record a summary event and continue

        tag_mod_report = ModificationReport.get_instance()
        tag_mod_report.add_error_modification(
            kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
            error_message=(
                f"global unavailable threshold exceeded: "
                f"{self._unavailable.count} >= {threshold}"
            ),
            error_category="GLOBAL_THRESHOLD",
            extra={
                "unavailable_count": self._unavailable.count,
                "threshold": threshold,
            },
        )
        # Write a small summary file for operator inspection

        self._unavailable.write_summary()

    @typechecked
    def notify_album_marked_unavailable(
        self, album_wrapper: AlbumResponseWrapper
    ) -> None:
        """Notify collection that an album was marked unavailable.

        This updates internal counters and triggers a global policy evaluation.
        """
        album_id = album_wrapper.get_album_uuid()

        # Use wrapper identity (by album id) for membership; avoid double-counting
        added = self._unavailable.add(album_wrapper)
        if not added:
            return

        log(
            f"Album {album_id} marked unavailable "
            f"(total_unavailable={self._unavailable.count}).",
            level=LogLevel.FOCUS,
        )

        # Evaluate global policy after this change

        self._evaluate_global_policy()

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
                f"Integrity check failed in _handle_duplicate_album_conflict: "
                f"album names differ ('{name_existing}' vs '{name_incoming}'). "
                f"Context: {context}"
            )
        from immich_autotag.config.internal_config import (
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
        else:
            from immich_autotag.config.dev_mode import is_development_mode

            if is_development_mode():
                raise RuntimeError(
                    f"Duplicate album name detected when adding album: "
                    f"{existing_album.get_album_name()!r}"
                )
        collect_duplicate(
            self._collected_duplicates, existing_album, incoming_album, context
        )
        return existing_album

    @typechecked
    def delete_album(
        self,
        wrapper: AlbumResponseWrapper,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
        reason: str = "Album deleted",
    ) -> bool:
        """
        Deletes an album on the server and records the action, whether temporary or not.
        Returns True if deleted successfully or if it no longer exists.
        """

        from immich_autotag.api.immich_proxy.albums.get_album_info import proxy_delete_album
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        # Safety check: only allow deletion of temporary or duplicate albums
        if not wrapper.is_temporary_album():
            # Only allow deletion if it is a duplicate
            if not wrapper.is_duplicate_album():
                raise RuntimeError(
                    f"Refusing to delete album "
                    f"'{wrapper.get_album_name()}' (id={wrapper.get_album_uuid()}): "
                    "not a temporary or duplicate album."
                )
        # Remove locally first to avoid errors if already deleted
        self.remove_album_local_public(wrapper)
        try:
            proxy_delete_album(album_id=wrapper.get_album_uuid(), client=client)
        except Exception as exc:
            msg = str(exc)
            # Try to give a more specific reason if possible
            err_reason = "Unknown error"
            from typing import Any, cast

            response = None
            code = None
            # Try to access response and status_code directly, fallback to None
            try:
                response = cast(Any, exc).response
                code = response.status_code if response is not None else None
            except Exception:
                response = None
                code = None
            if code is not None:
                if code == 404:
                    err_reason = "Album not found (already deleted)"
                elif code == 400:
                    err_reason = "Album not empty or bad request"
                elif code == 403:
                    err_reason = "Permission denied"
                else:
                    err_reason = f"HTTP {code}"
            else:
                if "not found" in msg.lower():
                    err_reason = "Album not found (already deleted)"
                elif "not empty" in msg.lower():
                    err_reason = "Album not empty"
                elif "permission" in msg.lower() or "forbidden" in msg.lower():
                    err_reason = "Permission denied"
            log(
                f"Failed to delete album "
                f"'{wrapper.get_album_name()}' (id={wrapper.get_album_uuid()}). "
                f"Reason: {err_reason}. Exception: {msg}",
                level=LogLevel.WARNING,
            )
            raise RuntimeError(
                f"Failed to delete album "
                f"'{wrapper.get_album_name()}' (id={wrapper.get_album_uuid()}). "
                f"Reason: {err_reason}."
            ) from exc
        from immich_autotag.report.modification_kind import ModificationKind

        # On success, err_reason is not set, so use a default
        tag_mod_report.add_album_modification(
            kind=ModificationKind.DELETE_ALBUM,
            album=wrapper,
            old_value=wrapper.get_album_name(),
            extra={"reason": f"{reason} (SUCCESS)"},
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
        name: str,
    ) -> None:
        """
        Handles the case of a non-temporary duplicate:
        error in development, collection in other modes.
        """

        from immich_autotag.config.internal_config import (
            MERGE_DUPLICATE_ALBUMS_ENABLED,
        )

        if MERGE_DUPLICATE_ALBUMS_ENABLED:
            # Centralizes handling in the unified method
            self._handle_duplicate_album_conflict(
                incoming_album=incoming_album,
                existing_album=existing,
                context="duplicate_on_load",
            )
            return

        if is_development_mode():
            raise RuntimeError(
                f"Duplicate album name detected when adding album: {name!r}"
            )
            return  # Unreachable but helps mypy
            return  # Unreachable but helps mypy

        # Default behavior: collect duplicate report
        from immich_autotag.albums.duplicates.duplicate_album_reports import (
            DuplicateAlbumReport,
        )

        self._collected_duplicates.append(
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

    @typechecked
    def _try_append_wrapper_to_list(
        self,
        *,
        wrapper: AlbumResponseWrapper,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
        old_tested_mode: bool = True,
    ) -> AlbumResponseWrapper | None:
        """Central helper: attempt to append a wrapper to an albums list with duplicate handling.

        If a duplicate name exists and it's a temporary album,
        attempt to delete the duplicate on the server (if `client` is provided)
        and skip adding. If it's a non-temporary duplicate, raise RuntimeError.
        This centralizes duplicate detection used during initial load and
        during runtime album creation.
        """
        albums_list = self._albums  # Access the internal dual map
        albums_list.add(wrapper)
        name = wrapper.get_album_name()
        if self.is_duplicated(wrapper):

            # Temporary duplicate
            if is_temporary_album(name):
                # Only call delete_album if client is of correct type
                if self.delete_album(
                    wrapper=wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                    reason="Removed duplicate temporary album during add",
                ):
                    return None

            else:
                if old_tested_mode:
                    # we cannot use this, we do not have
                    # Combine all duplicates into one
                    surviving_album = self.combine_duplicate_albums(
                        list(self.find_all_albums_with_name(name)),
                        context="duplicate_on_create",
                    )
                    # After combining, check if any duplicates remain
                    albums_after = list(self.find_all_albums_with_name(name))
                    assert surviving_album in albums_after
                    if len(albums_after) == 1:
                        return albums_after[0]
                    else:
                        # Raise exception for developers after cleanup
                        raise RuntimeError(
                            f"Duplicate albums with name '{name}' were found and combined, "
                            f"but multiple still remain. This indicates a data integrity issue. "
                            f"Review the logs and investigate the cause."
                        )
                else:
                    # Non-temporary duplicate
                    existing = self.find_first_album_with_name(name)
                    if existing is not None:
                        self._handle_non_temporary_duplicate(
                            existing=existing,
                            incoming_album=wrapper,
                            tag_mod_report=tag_mod_report,
                            name=name,
                        )
                        return None
        return wrapper

    @typechecked
    def _add_album_wrapper(
        self,
        wrapper: AlbumResponseWrapper,
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
                f"Cannot add album: an album with the name '{name}' already exists "
                f"(id={existing.get_album_uuid()})."
            )
        # Append to collection and update maps
        self._albums.add(wrapper)
        # Optionally update asset-to-albums map or other structures here if needed
        return wrapper

    @typechecked
    def get_asset_to_albums_map(self) -> AssetToAlbumsMap:
        """
        Returns the current asset-to-albums map, building it if not already done.
        Defensive: always returns AssetToAlbumsMap, never None.
        """
        self._ensure_fully_loaded()
        if self._asset_to_albums_map is None:
            self._rebuild_asset_to_albums_map()
        if self._asset_to_albums_map is None:
            # If still None after rebuild, this is a fatal error
            raise RuntimeError(
                "AssetToAlbumsMap is None after rebuild. This should never happen."
            )
        return self._asset_to_albums_map

    @conditional_typechecked
    def albums_for_asset(
        self, asset: AssetResponseWrapper
    ) -> Iterable[AlbumResponseWrapper]:
        """
        Returns an iterable of AlbumResponseWrapper objects for all albums
        the asset belongs to (O(1) lookup via map). Ensures all albums are loaded before proceeding.
        """
        return self.get_asset_to_albums_map().get_from_uuid(asset.get_id())

    @conditional_typechecked
    def album_names_for_asset(self, asset: AssetResponseWrapper) -> list[str]:
        """Returns the names of the albums the asset belongs to.
        Use this only if you need names (e.g., for logging).
        Prefer albums_for_asset() for object access.
        """

        return [w.get_album_name() for w in self.albums_for_asset(asset)]

    @conditional_typechecked
    def albums_wrappers_for_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> Iterable[AlbumResponseWrapper]:
        """
        Returns an iterable of AlbumResponseWrapper objects for all albums
        the asset (wrapped or raw) belongs to. Accepts either AssetResponseWrapper or AssetResponseDto.
        """

        return self.albums_for_asset(asset_wrapper)

    # Duplicate method albums_with_name removed

    # remove_album deleted: use delete_album and _remove_album_from_local_collection
    @typechecked
    def find_all_albums_with_name(
        self, album_name: str
    ) -> Iterable[AlbumResponseWrapper]:
        """
        Yields all non-deleted AlbumResponseWrapper objects with the given name.
        Returns a generator (may yield none).
        Optimized: uses AlbumDualMap for O(1) lookup, then filters deleted.
        """
        self._ensure_fully_loaded()
        # AlbumNameMap only supports one album per name, but if there are duplicates, the structure would need to be changed.
        # If the map only supports one, we maintain compatibility by returning a list of one or zero.
        album = self._albums.get_by_name(album_name)
        if album and not album.is_deleted():
            yield album

    @typechecked
    def combine_duplicate_albums(
        self, albums: list[AlbumResponseWrapper], context: str
    ) -> AlbumResponseWrapper:
        """
        Combines a list of duplicate albums into one, applying a reduction algorithm:
        merges all albums two by two using the duplicate policy, always keeping the surviving album,
        until only one remains. The 'context' argument is mandatory and must indicate the origin or
        reason for the combination (for logs, exceptions, etc). Returns the resulting final album.
        """
        if not albums:
            raise ValueError(
                f"No albums provided to combine_duplicate_albums (context: {context})"
            )
        # Safety: Ensure all albums are true duplicates before merging
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

    @typechecked
    def _add_user_to_album(
        self,
        album: AlbumResponseWrapper,
        user: UserResponseWrapper,
        context: ImmichContext,
        tag_mod_report: ModificationReport,
    ) -> None:
        """
        Public helper to add a user as EDITOR to an album. Handles only user addition, error reporting, and event logging.
        """

        from immich_client.models.album_user_role import AlbumUserRole

        from immich_autotag.api.logging_proxy.albums.album_permissions import (
            logging_add_user_to_album,
        )

        try:
            logging_add_user_to_album(
                album=album,
                user=user,
                access_level=AlbumUserRole.EDITOR,
                context=context,
            )
        except Exception as e:
            raise RuntimeError(
                f"Error adding user {user.get_uuid()} as EDITOR to album {album.get_album_uuid()} "
                f"('{album.get_album_name()}'): {e}"
            ) from e

    @typechecked
    def _create_album_dto(
        self,
        album_name: str,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
    ) -> AlbumResponseDto:
        """
        Private helper to create an album via the API. Returns the album object. Handles creation, error reporting, and event logging.
        """
        from immich_client.models.create_album_dto import CreateAlbumDto

        from immich_autotag.api.immich_proxy.proxy_create_album import (
            proxy_create_album,
        )

        album = proxy_create_album(
            client=client,
            body=CreateAlbumDto(album_name=album_name),
        )
        return album

    def _album_wrapper_from_partial_dto(
        self, album: AlbumResponseDto
    ) -> AlbumResponseWrapper:
        """
        Centralized helper to create an AlbumResponseWrapper from a partial AlbumResponseDto.
        Use this method instead of calling AlbumResponseWrapper.from_partial_dto directly.
        """
        return AlbumResponseWrapper.from_partial_dto(album)

    @conditional_typechecked
    def create_or_get_album_with_user(
        self,
        album_name: str,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
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
            self.combine_duplicate_albums(albums_found, context="duplicate_on_create")
            # Raise exception for developers after cleanup
            raise RuntimeError(
                f"Duplicate albums with name '{album_name}' were found and combined. This indicates a data integrity issue. Review the logs and investigate the cause."
            )

        # If it doesn't exist, create it and assign user
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper

        album = self._create_album_dto(album_name, client, tag_mod_report)

        # Centralized user access
        user_wrapper_opt = UserResponseWrapper.load_current_user()
        if user_wrapper_opt is None:
            raise RuntimeError(
                "Could not load current user (UserResponseWrapper.load_current_user() returned None)"
            )
        user_wrapper: UserResponseWrapper = user_wrapper_opt

        wrapper = self._album_wrapper_from_partial_dto(album)
        tag_mod_report.add_album_modification(
            kind=ModificationKind.CREATE_ALBUM,
            album=wrapper,
            extra={"created": True},
        )
        self._add_album_wrapper(wrapper)
        # Assign user as EDITOR if not already owner
        if wrapper.get_owner_uuid() != user_wrapper.get_uuid():
            from immich_autotag.context.immich_context import ImmichContext

            context = ImmichContext.get_default_instance()
            self._add_user_to_album(
                album=wrapper,
                user=user_wrapper,
                context=context,
                tag_mod_report=tag_mod_report,
            )
        return wrapper

    @classmethod
    def resync_from_api_class(cls) -> None:
        """
        Class wrapper to maintain compatibility: calls the instance method on the singleton.
        """
        instance = cls.get_instance()
        instance.resync_from_api()

    @typechecked
    def find_album_by_id(self, album_id: UUID) -> AlbumResponseWrapper | None:
        """
        Returns the first album with the given UUID, or None if not found.
        """
        for album in self.get_albums():
            if str(album.get_album_uuid()) == str(album_id):
                return album
        return None

    @typechecked
    def resync_from_api(self, clear_first: bool = True) -> None:
        """
        Reloads the album collection from the API, same as from_client but on the current instance.
        - Downloads all albums from the API (initially without assets).
        - If clear_first is True (default), clears and rebuilds the local collection.
        - If clear_first is False, merges new albums with existing ones (without deleting current ones).
        - Handles duplicates and logging same as from_client.
        """
        from immich_autotag.api.immich_proxy.albums.get_all_albums import proxy_get_all_albums
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log
        from immich_autotag.report.modification_report import ModificationReport

        # Set sync state to SYNCING at the start
        self._sync_state = SyncState.SYNCING
        client = self.get_client()
        tag_mod_report = ModificationReport.get_instance()
        assert isinstance(tag_mod_report, ModificationReport)

        albums = proxy_get_all_albums(client=client)
        # Clear previous duplicates before reloading
        self._collected_duplicates.clear()

        log(
            f"[RESYNC] Starting album resync. Total albums to process: {len(albums)}",
            level=LogLevel.PROGRESS,
        )
        # Integrate PerformanceTracker for progress and estimated time
        from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker.from_args(
            total_assets=len(albums), max_assets=len(albums), skip_n=0
        )

        if clear_first:
            # Clear the current collection
            self._albums.clear()
        # Rebuild the collection same as from_client
        for idx, album in enumerate(albums, 1):
            wrapper = self._album_wrapper_from_partial_dto(album)
            # If clear_first, just add; if not, only add if it does not exist
            if clear_first or not self.find_first_album_with_name(
                wrapper.get_album_name()
            ):
                self._try_append_wrapper_to_list(
                    wrapper=wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                )
                # Log progress and estimated time
                if tracker.should_log_progress(idx):
                    progress_msg = tracker.get_progress_description(idx)
                    log(
                        f"[ALBUM-LOAD][API-BULK] {progress_msg} | Album: '{wrapper.get_album_name()}' processed after bulk fetch with {len(albums)} assets.",
                        level=LogLevel.INFO,
                    )

        tag_mod_report.flush()
        if len(self._collected_duplicates) > 0:
            from immich_autotag.albums.duplicates.write_duplicates_summary import (
                write_duplicates_summary,
            )

            write_duplicates_summary(self._collected_duplicates)

        log(f"[RESYNC] Total albums: {len(self)}", level=LogLevel.INFO)
        # Mark as synchronized
        self._sync_state = SyncState.SYNCED

    @typechecked
    def is_duplicated(self, wrapper: "AlbumResponseWrapper") -> bool:
        """
        Returns True if an album with the same name as 'wrapper' exists in the collection.
        """
        name = wrapper.get_album_name()
        names = self.find_all_albums_with_name(name)
        return len(list(names)) > 1

    @classmethod
    def from_client(cls) -> "AlbumCollectionWrapper":
        """
        Instantiates the singleton and loads albums from the API using the default client.
        Returns the singleton instance.
        """
        instance = cls()
        instance.resync_from_api()
        return instance

    def __len__(self) -> int:
        """
        Returns the number of albums in the collection (including deleted unless
        filtered elsewhere).
        """
        return len(self._albums)

    # Removed broken is_owner method (should be on AlbumResponseWrapper)


# Singleton instance storage


_album_collection_singleton: AlbumCollectionWrapper | None = None
