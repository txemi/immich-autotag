from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.report.modification_entry import ModificationEntry

if TYPE_CHECKING:
    from immich_autotag.albums.albums.asset_map_manager.manager import AssetMapManager

    from immich_autotag.albums.albums.duplicates_manager.manager import (
        DuplicateAlbumManager,
    )

from enum import Enum, auto
from typing import Iterable
from uuid import UUID

import attrs
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.albums.album.album_cache_entry import AlbumCacheEntry
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_and_modification import (
    AlbumAndModification,
)
from immich_autotag.albums.albums.album_dual_map import AlbumDualMap
from immich_autotag.albums.albums.album_list import AlbumList
from immich_autotag.albums.albums.asset_to_albums_map import AssetToAlbumsMap
from immich_autotag.albums.albums.unavailable_manager.manager import (
    UnavailableAlbumManager,
)
from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
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
    # Asset map manager (delegates all asset-to-albums mapping logic)
    _asset_map_manager: "AssetMapManager | None" = attrs.field(
        init=False,
        default=None,
        repr=False,
        eq=False,
    )

    # Unavailable album manager (delegates all unavailable logic)
    _unavailable_manager: "UnavailableAlbumManager | None" = attrs.field(
        init=False,
        default=None,
        repr=False,
        eq=False,
    )

    # Duplicate album manager (delegates all duplicate logic)
    _duplicate_manager: "DuplicateAlbumManager | None" = attrs.field(
        init=False,
        default=None,
        repr=False,
        eq=False,
    )

    # Enum to indicate sync state: NOT_STARTED, SYNCING, SYNCED
    _sync_state: SyncState = attrs.field(
        default=SyncState.NOT_STARTED,
        init=False,
        repr=False,
    )

    # Cached asset-to-albums map for batch processing
    _batch_asset_to_albums_map: AssetToAlbumsMap | None = attrs.field(
        init=False,
        default=None,
        repr=False,
        eq=False,
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

    def _get_asset_map_manager(self) -> "AssetMapManager":
        if self._asset_map_manager is None:
            from immich_autotag.albums.albums.asset_map_manager.manager import (
                AssetMapManager,
            )

            self._asset_map_manager = AssetMapManager(self)
        return self._asset_map_manager

    def _get_temporary_album_manager(self):
        """
        Returns an instance of TemporaryAlbumManager bound to this collection.
        """
        from immich_autotag.assets.albums.temporary_manager.manager import (
            TemporaryAlbumManager,
        )

        return TemporaryAlbumManager(self)

    def prepare_batch_asset_to_albums_map(self):
        """
        Precompute and cache the asset-to-albums map for the current batch. Also performs cleanup of empty temporary albums once.
        """
        self._ensure_fully_loaded()
        temp_manager = self._get_temporary_album_manager()
        temp_manager.cleanup_empty_temporary_albums(self.get_client())
        asset_map_manager = self._get_asset_map_manager()
        self._batch_asset_to_albums_map = asset_map_manager.get_map()

    def clear_batch_asset_to_albums_map(self):
        """
        Clear the cached asset-to-albums map after batch processing.
        """
        self._batch_asset_to_albums_map = None

    def _get_duplicate_album_manager(self) -> "DuplicateAlbumManager":
        if self._duplicate_manager is None:
            from immich_autotag.albums.albums.duplicates_manager.manager import (
                DuplicateAlbumManager,
            )

            self._duplicate_manager = DuplicateAlbumManager(collection=self)
        return self._duplicate_manager

    def log_lazy_load_timing(self):
        import time

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
        global _album_collection_singleton
        if _album_collection_singleton is not None:
            raise RuntimeError(
                "AlbumCollectionWrapper singleton violation: a second instance was created. "
                "Use AlbumCollectionWrapper.get_instance() to access the singleton."
            )
        _album_collection_singleton = self
        # Asset map is built on demand, not during initialization

    @classmethod
    def get_instance(cls) -> "AlbumCollectionWrapper":
        global _album_collection_singleton
        if _album_collection_singleton is None:
            # Create and sync the singleton instance
            _album_collection_singleton = cls()
            _album_collection_singleton.resync_from_api()
        return _album_collection_singleton

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
        self._get_asset_map_manager()._remove_album(album_wrapper)
        self._albums.remove(album_wrapper)
        return True

    @typechecked
    def build_asset_map(self) -> AssetToAlbumsMap:
        """Delegates asset map build to AssetMapManager."""
        return self._get_asset_map_manager()._build_map()

    @typechecked
    def _rebuild_asset_map(self) -> None:
        """Delegates asset map rebuild to AssetMapManager."""
        self._get_asset_map_manager().rebuild_map()

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

    # Removed broken is_owner method (should be on AlbumResponseWrapper)

    def _get_unavailable_album_manager(self) -> "UnavailableAlbumManager":
        if self._unavailable_manager is None:
            from immich_autotag.albums.albums.unavailable_manager.manager import (
                UnavailableAlbumManager,
            )

            self._unavailable_manager = UnavailableAlbumManager(self)
        return self._unavailable_manager

    @typechecked
    def notify_album_marked_unavailable(
        self, album_wrapper: AlbumResponseWrapper
    ) -> None:
        """Notify collection that an album was marked unavailable.
        Delegates to UnavailableAlbumManager.
        """
        self._get_unavailable_album_manager().notify_album_marked_unavailable(
            album_wrapper
        )

    @typechecked
    # Duplicate conflict logic delegated to manager
    def delete_album(
        self,
        wrapper: AlbumResponseWrapper,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
        reason: str = "Album deleted",
        remove_from_map: bool = True,
    ) -> ModificationEntry:
        """
        Deletes an album on the server and records the action, whether temporary or not.
        Returns True if deleted successfully or if it no longer exists.
        """

        from immich_autotag.api.immich_proxy.albums.delete_album import (
            proxy_delete_album,
        )

        # Safety check: only allow deletion of temporary or duplicate albums
        if not wrapper.is_temporary_album():
            # Only allow deletion if it is a duplicate
            if not wrapper.is_duplicate_album():
                raise RuntimeError(
                    f"Refusing to delete album "
                    f"'{wrapper.get_album_name()}' (id={wrapper.get_album_uuid()}) "
                    "not a temporary or duplicate album."
                )
        # Remove locally first to avoid errors if already deleted

        if remove_from_map:
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
            if err_reason == "Album not found (already deleted)":
                # Album is already deleted, treat as success
                raise RuntimeError(
                    f"Album '{wrapper.get_album_name()}' (id={wrapper.get_album_uuid()}) "
                    "already deleted."
                )
            else:
                raise RuntimeError(
                    f"Failed to delete album "
                    f"'{wrapper.get_album_name()}' (id={wrapper.get_album_uuid()}). "
                    f"Reason: {err_reason}."
                ) from exc
        from immich_autotag.report.modification_kind import ModificationKind

        # On success, err_reason is not set, so use a default
        report_entry: ModificationEntry = tag_mod_report.add_album_modification(
            kind=ModificationKind.DELETE_ALBUM,
            album=wrapper,
            old_value=wrapper.get_album_name(),
            extra={"reason": f"{reason} (SUCCESS)"},
        )
        return report_entry

    def remove_album_local_public(self, album_wrapper: AlbumResponseWrapper) -> bool:
        """
        Public wrapper for _remove_album_from_local_collection.
        """
        return self._remove_album_from_local_collection(album_wrapper)

    @typechecked
    def _combine_duplicate_albums(
        self, albums: list[AlbumResponseWrapper], context: str
    ) -> AlbumAndModification:
        # The manager now returns AlbumAndModification, but this method expects AlbumResponseWrapper

        result: AlbumAndModification = (
            self._get_duplicate_album_manager().combine_duplicate_albums(
                albums, context
            )
        )
        return result

    @typechecked
    # Non-temporary duplicate logic delegated to manager
    def _try_append_wrapper_to_list(
        self,
        *,
        album_wrapper: AlbumResponseWrapper,
        client: ImmichClient,
        tag_mod_report: ModificationReport,
        old_tested_mode: bool = True,
    ) -> AlbumAndModification:
        """Central helper: attempt to append an album wrapper to the albums list with duplicate handling.

        If a duplicate name exists and it's a temporary album,
        attempt to delete the duplicate on the server (if `client` is provided)
        and skip adding. If it's a non-temporary duplicate, raise RuntimeError.
        This centralizes duplicate detection used during initial load and
        during runtime album creation.
        """
        albums_list = self._albums  # Access the internal dual map
        album_id = album_wrapper.get_album_uuid()
        # First, check for existing by ID
        try:
            existing_by_id = albums_list.get_by_id(album_id)
        except Exception:
            existing_by_id = None
        if existing_by_id is not None:
            # Compare and keep the best
            best = existing_by_id.get_best_cache_entry(album_wrapper)
            if best is not existing_by_id:
                albums_list.remove(existing_by_id)
                albums_list.add(best)
            return AlbumAndModification.from_album(best)

        album_name = album_wrapper.get_album_name()
        existing_album = self.find_first_album_with_name(album_name)
        if existing_album is None:
            # Only add if not present
            albums_list.add(album_wrapper)

            return AlbumAndModification.from_album(album_wrapper)
        # There is already an album with this name: treat as duplicate
        if is_temporary_album(album_name):
            # Delete the temporary duplicate
            report_entry: ModificationEntry | None = self.delete_album(
                wrapper=album_wrapper,
                client=client,
                tag_mod_report=tag_mod_report,
                reason="Removed duplicate temporary album during add",
                remove_from_map=False,  # Not in map yet, so skip local removal
            )
            albums_after = list(self.find_all_albums_with_name(album_name))
            if len(albums_after) == 1:
                return AlbumAndModification.from_album_and_entry(
                    albums_after[0], report_entry
                )
            else:
                raise RuntimeError(
                    f"Duplicate albums with name '{album_name}' were found and attempted to delete, "
                    f"but multiple still remain. This indicates a data integrity issue. "
                    f"Review the logs and investigate the cause."
                )
        if old_tested_mode:
            # Merge all duplicates into one, including the new album_wrapper
            found_albums = list(self.find_all_albums_with_name(album_name))
            combined_albums = found_albums + [album_wrapper]
            surviving_album = self._combine_duplicate_albums(
                combined_albums,
                context="duplicate_on_create",
            )
            albums_after = list(self.find_all_albums_with_name(album_name))
            if surviving_album not in albums_after:
                raise RuntimeError(
                    f"Surviving album after combining duplicates with name '{album_name}' "
                    "is not present in the collection. This indicates a data integrity issue."
                )

            #
            # Duplicates created by the user (not temporary, not system-generated) are not supported by design.
            # There is no robust, general way to resolve user-created album duplicates automatically without risking data loss or undefined behavior.
            # For now, the safest approach is to raise an exception and fail fast, so the problem is visible and can be fixed manually.
            # The 'crazy_debug_mode' is a development/testing switch, but this strict behavior is likely to remain permanent unless a clear, robust merge policy is defined for user duplicates.
            # Any attempt to "survive" user duplicates with ad-hoc logic is fragile and discouraged.
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(
                f"[WARNING] Album duplicate detected: An album with the name '{album_name}' already exists, and this duplicate was created by the user (not a temporary/system album).\n"
                "This situation cannot be resolved automatically by the application, as merging or deleting user-created albums could result in data loss or unexpected behavior.\n"
                "Please review your albums in the Immich app or web interface, y manually rename or remove the duplicate(s) to ensure each album name is unique.\n"
                "If you are a developer, see the code and comments in AlbumCollectionWrapper for more details about this design decision.",
                level=LogLevel.WARNING,
            )
            # Continue execution: rename and add as below

            from immich_autotag.albums.albums.duplicates_manager.rename_strategy.rename_duplicate_album import (
                rename_duplicate_album,
            )

            report_entry = rename_duplicate_album(album_wrapper, client, tag_mod_report)

            albums_list.add(album_wrapper)
            return AlbumAndModification.from_album(album_wrapper)

        else:
            # Non-temporary duplicate: log and skip
            #
            # NOTE: I am not at all convinced that this logic actually solves anything meaningful.
            # Honestly, I don't know what to think about this case, so this branch is effectively deactivated.
            # The proliferation of duplicate-handling logic throughout the codebase is a mess, and I don't yet have a clear or robust solution.
            # For now, let's do the sensible thing, fail fast on user duplicates, and hope to simplify this code over time as we better understand the real-world scenarios.
            result: (
                AlbumAndModification
            ) = self._get_duplicate_album_manager().handle_non_temporary_duplicate(
                existing=existing_album,
                incoming_album=album_wrapper,
                tag_mod_report=tag_mod_report,
                name=album_name,
            )
            # result now contains both the album and any modifications, propagate as needed
            return result

    @typechecked
    def _add_album_wrapper(
        self,
        album_wrapper: AlbumResponseWrapper,
    ) -> AlbumResponseWrapper:
        """Add an album wrapper to this collection with centralized duplicate handling.

        If a duplicate exists and is temporary, attempt to delete it on the server
        and remove it locally before adding the provided album wrapper. If duplicate is
        non-temporary, raise RuntimeError.
        """
        album_name = album_wrapper.get_album_name()
        existing_album = self.find_first_album_with_name(album_name)
        if existing_album is not None:
            raise RuntimeError(
                f"Cannot add album: an album with the name '{album_name}' already exists "
                f"(id={existing_album.get_album_uuid()})."
            )
        # Append to collection and update maps
        self._albums.add(album_wrapper)
        # Optionally update asset-to-albums map or other structures here if needed
        return album_wrapper

    @typechecked
    def get_asset_to_albums_map(self) -> AssetToAlbumsMap:
        """
        Returns the current asset-to-albums map. Uses cached map if available, otherwise builds without cleanup.
        Defensive: always returns AssetToAlbumsMap, never None.
        """
        if self._batch_asset_to_albums_map is not None:
            return self._batch_asset_to_albums_map
        self._ensure_fully_loaded()
        asset_map_manager = self._get_asset_map_manager()
        return asset_map_manager.get_map()

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

        from immich_autotag.api.immich_proxy.albums import proxy_create_album

        album = proxy_create_album(
            client=client,
            body=CreateAlbumDto(album_name=album_name),
        )
        return album

    @typechecked
    def _get_or_create_partial_album_wrapper(
        self, partial_dto: AlbumResponseDto
    ) -> AlbumResponseWrapper:
        """
        Returns an AlbumResponseWrapper for a partial AlbumResponseDto (SEARCH mode).
        Ensures singleton and cache logic are respected. The DTO is always treated as partial (SEARCH).
        """
        from immich_autotag.albums.album.album_dto_state import (
            AlbumDtoState,
            AlbumLoadSource,
        )
        from immich_autotag.types.uuid_wrappers import AlbumUUID

        album_id = partial_dto.id
        album_uuid = AlbumUUID(album_id)
        try:
            cache_entry_wrapper = self._albums.get_by_id(album_uuid)
        except RuntimeError:
            cache_entry_wrapper = None
        if cache_entry_wrapper is not None:
            existing_wrapper = cache_entry_wrapper
            new_state = AlbumDtoState.create(
                dto=partial_dto, load_source=AlbumLoadSource.SEARCH
            )
            new_entry = AlbumCacheEntry.create(dto=new_state)
            best_wrapper = existing_wrapper.get_best_cache_entry(
                AlbumResponseWrapper(new_entry)
            )
            if best_wrapper is not existing_wrapper:
                self._albums.remove(existing_wrapper)
                self._albums.add(best_wrapper)
                return best_wrapper
            return existing_wrapper
        state = AlbumDtoState.create(
            dto=partial_dto, load_source=AlbumLoadSource.SEARCH
        )
        cache_entry_obj = AlbumCacheEntry.create(dto=state)
        wrapper = AlbumResponseWrapper(cache_entry_obj)
        self._albums.add(wrapper)
        return wrapper

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
            self._combine_duplicate_albums(albums_found, context="duplicate_on_create")
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

        album_wrapper = self._get_or_create_partial_album_wrapper(album)
        # don above:          self._add_album_wrapper(album_wrapper)
        tag_mod_report.add_album_modification(
            kind=ModificationKind.CREATE_ALBUM,
            album=album_wrapper,
            extra={"created": True},
        )
        # Assign user as EDITOR if not already owner
        if album_wrapper.get_owner_uuid() != user_wrapper.get_uuid():
            from immich_autotag.context.immich_context import ImmichContext

            context = ImmichContext.get_default_instance()
            self._add_user_to_album(
                album=album_wrapper,
                user=user_wrapper,
                context=context,
                tag_mod_report=tag_mod_report,
            )
        return album_wrapper

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

    def _clear(self):
        # Clear the current collection
        # Clear previous duplicates before reloading
        self._get_duplicate_album_manager().collected_duplicates.clear()
        self._get_asset_map_manager().clear()
        self._albums.clear()

    @typechecked
    def resync_from_api(self, clear_first: bool = True) -> None:
        """
        Reloads the album collection from the API, same as _from_client but on the current instance.
        - Downloads all albums from the API (initially without assets).
        - If clear_first is True (default), clears and rebuilds the local collection.
        - If clear_first is False, merges new albums with existing ones (without deleting current ones).
        - Handles duplicates and logging same as _from_client.
        """
        from immich_autotag.api.immich_proxy.albums.get_all_albums import (
            proxy_get_all_albums,
        )
        from immich_autotag.report.modification_report import ModificationReport

        # Set sync state to SYNCING at the start
        self._sync_state = SyncState.SYNCING
        client = self.get_client()
        tag_mod_report = ModificationReport.get_instance()
        assert isinstance(tag_mod_report, ModificationReport)

        albums = proxy_get_all_albums(client=client)

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
            self._clear()
        # Rebuild the collection same as _from_client
        for idx, album in enumerate(albums, 1):
            album_wrapper = self._get_or_create_partial_album_wrapper(album)
            # If clear_first, just add; if not, only add if it does not exist
            if clear_first or not self.find_first_album_with_name(
                album_wrapper.get_album_name()
            ):
                self._try_append_wrapper_to_list(
                    album_wrapper=album_wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                )
                # Log progress and estimated time
                if tracker.should_log_progress(idx):
                    progress_msg = tracker.get_progress_description(idx)
                    album_url = album_wrapper.get_immich_album_url().geturl()
                    log(
                        f"[ALBUM-LOAD][API-BULK] {progress_msg} | Album: '{album_wrapper.get_album_name()}' | URL: {album_url} processed after bulk fetch with {len(albums)} assets.",
                        level=LogLevel.PROGRESS,
                    )

        tag_mod_report.flush()
        if len(self._get_duplicate_album_manager().collected_duplicates) > 0:
            from immich_autotag.albums.duplicates.write_duplicates_summary import (
                write_duplicates_summary,
            )

            write_duplicates_summary(
                self._get_duplicate_album_manager().collected_duplicates
            )

        log(f"[RESYNC] Total albums: {len(self)}", level=LogLevel.INFO)
        # Mark as synchronized
        self._sync_state = SyncState.SYNCED

    @typechecked
    def is_duplicated(self, wrapper: "AlbumResponseWrapper") -> bool:
        return self._get_duplicate_album_manager().is_duplicated(wrapper)

    def __len__(self) -> int:
        """
        Returns the number of albums in the collection (including deleted unless
        filtered elsewhere).
        """
        return len(self._albums)


# Singleton instance storage


_album_collection_singleton: AlbumCollectionWrapper | None = None
