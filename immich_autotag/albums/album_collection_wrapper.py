from __future__ import annotations

import attrs
from immich_client.models.asset_response_dto import AssetResponseDto
from typeguard import typechecked

from immich_autotag.albums.album_list import AlbumList
from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.asset_to_albums_map import AssetToAlbumsMap

try:
    # Prefer absolute import, but fall back to a package-relative import for
    # environments where absolute package resolution may fail (CI, certain test runners).
    from immich_autotag.assets.albums.temporary_albums import is_temporary_album
except Exception:
    from ..assets.albums.temporary_albums import is_temporary_album

# Import for type checking and runtime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient
from immich_autotag.utils.decorators import conditional_typechecked

# Singleton instance storage
_album_collection_singleton: AlbumCollectionWrapper | None = None


@attrs.define(auto_attribs=True, slots=True)
class AlbumCollectionWrapper:

    albums: AlbumList = attrs.field(validator=attrs.validators.instance_of(AlbumList))
    _asset_to_albums_map: AssetToAlbumsMap = attrs.field(
        init=False,
        factory=AssetToAlbumsMap,
        validator=attrs.validators.instance_of(AssetToAlbumsMap),
    )
    # Count of albums marked unavailable during this run
    _unavailable_count: int = attrs.field(default=0, init=False, repr=False)
    # Track unavailable album wrappers to avoid double-counting
    _unavailable_albums: set[AlbumResponseWrapper] = attrs.field(
        default=attrs.Factory(set), init=False, repr=False
    )

    def __attrs_post_init__(self):
        global _album_collection_singleton
        if _album_collection_singleton is not None:
            raise RuntimeError(
                "AlbumCollectionWrapper is a singleton: only one instance is allowed."
            )
        _album_collection_singleton = self
        self._rebuild_asset_to_albums_map()

    @typechecked
    def _rebuild_asset_to_albums_map(self):
        """Rebuilds the asset-to-albums map from scratch."""

        self._asset_to_albums_map = self._asset_to_albums_map_build()

    @typechecked
    def _add_album_to_map(self, album_wrapper: AlbumResponseWrapper):
        for asset_id in album_wrapper.get_asset_ids():
            if asset_id not in self._asset_to_albums_map:
                self._asset_to_albums_map[asset_id] = AlbumList()
            self._asset_to_albums_map[asset_id].append(album_wrapper)

    @typechecked
    def _remove_album_from_map(self, album_wrapper: AlbumResponseWrapper):
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
        Elimina un álbum de la colección interna y actualiza el mapa incrementalmente. Devuelve True si se eliminó, False si no estaba.
        """
        if album_wrapper in self.albums:
            self.albums = [a for a in self.albums if a != album_wrapper]
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
    def notify_album_marked_unavailable(self, album_wrapper: AlbumResponseWrapper) -> None:
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
        if album_wrapper in self._unavailable_albums:
            return
        self._unavailable_albums.add(album_wrapper)
        try:
            self._unavailable_count += 1
        except Exception:
            self._unavailable_count = len(self._unavailable_albums)

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            f"Album {album_id} marked unavailable (total_unavailable={self._unavailable_count}).",
            level=LogLevel.FOCUS,
        )

        # Evaluate global policy after this change
        try:
            self._evaluate_global_policy()
        except Exception:
            # Bubble up in development mode, otherwise swallow to continue processing
            raise

    @typechecked
    def _ensure_unique_album_name(self, album_name: str) -> None:
        """Ensure no other album in the collection has the same name.

        Raises RuntimeError if a duplicate name is found. This enforces stricter
        correctness to avoid ambiguity in operations that rely on album names.
        """
        for w in self.albums:
            try:
                if w.get_album_name() == album_name:
                    raise RuntimeError(
                        f"Duplicate album name detected when adding album: {album_name!r}"
                    )
            except Exception:
                # If a wrapper misbehaves retrieving name, fail fast
                raise

    @typechecked
    def write_unavailable_summary(self) -> None:
        """Write a small JSON summary of unavailable albums for operator inspection."""
        try:
            import json
            from immich_autotag.utils.run_output_dir import get_run_output_dir

            summary_items = []
            def _unavailable_sort_key(w: AlbumResponseWrapper) -> str:
                try:
                    return w.get_album_id() or 
                except Exception:
                    return 

            for wrapper in sorted(self._unavailable_albums, key=_unavailable_sort_key):
                try:
                    album_id = wrapper.get_album_id()
                except Exception:
                    album_id = None
                try:
                    name = wrapper.get_album_name()
                except Exception:
                    name = None
                summary_items.append({"id": album_id, "name": name})

            out_dir = get_run_output_dir()
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "albums_unavailable_summary.json"
            with out_file.open("w", encoding="utf-8") as fh:
                json.dump({"count": len(summary_items), "albums": summary_items}, fh, indent=2)
        except Exception:
            # Best-effort summary; don't raise
            pass

    @typechecked
    def _evaluate_global_policy(self) -> None:
        """Evaluate global unavailable-albums policy and act according to config.

        In DEVELOPMENT mode this may raise to fail-fast. In PRODUCTION it logs and
        records a summary event.
        """
        try:
            from immich_autotag.config.internal_config import (
                GLOBAL_UNAVAILABLE_THRESHOLD,
                DEFAULT_ERROR_MODE,
            )
            from immich_autotag.config._internal_types import ErrorHandlingMode
            from immich_autotag.report.modification_report import ModificationReport
            from immich_autotag.tags.modification_kind import ModificationKind
        except Exception:
            return

        try:
            threshold = int(GLOBAL_UNAVAILABLE_THRESHOLD)
        except Exception:
            return

        if self._unavailable_count >= threshold:
            # In development: fail fast to surface systemic problems
            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise RuntimeError(
                    f"Too many albums marked unavailable during run: {self._unavailable_count} >= {threshold}. Failing fast (DEVELOPMENT mode)."
                )

            # In production: record a summary event and continue
            try:
                tag_mod_report = ModificationReport.get_instance()
                tag_mod_report.add_error_modification(
                    kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
                    error_message=f"global unavailable threshold exceeded: {self._unavailable_count} >= {threshold}",
                    error_category="GLOBAL_THRESHOLD",
                    extra={
                        "unavailable_count": self._unavailable_count,
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

        Antes de construir el mapa, fuerza la carga de asset_ids en todos los álbumes (lazy loading).
        """
        asset_map = AssetToAlbumsMap()
        assert (
            len(self.albums) > 0
        ), "AlbumCollectionWrapper must have at least one album to build asset map."
        albums_to_remove: list[AlbumResponseWrapper] = []
        from immich_autotag.context.immich_context import ImmichContext

        client = ImmichContext.get_default_client()
        for album_wrapper in self.albums:
            # Garantiza que el álbum está en modo full (assets cargados)
            # album_wrapper.ensure_full()
            if not album_wrapper.get_asset_ids():
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
                    albums_to_remove.append(album_wrapper)
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

        # Remove temporary albums after map build to avoid recursion
        if albums_to_remove:
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report = ModificationReport.get_instance()
            for album_wrapper in albums_to_remove:
                try:
                    # Log not-found removal in the modification report
                    if tag_mod_report:
                        tag_mod_report.add_album_modification(
                            kind=ModificationKind.DELETE_ALBUM,
                            album=album_wrapper,
                            old_value=album_wrapper.get_album_name(),
                            extra={
                                "reason": "Removed automatically after map build because it was empty and temporary"
                            },
                        )
                    self.remove_album(album_wrapper, client)
                except Exception as e:
                    album_name = album_wrapper.get_album_name()
                    from immich_autotag.logging.levels import LogLevel
                    from immich_autotag.logging.utils import log

                    log(
                        f"Failed to remove temporary album '{album_name}': {e}",
                        level=LogLevel.ERROR,
                    )
                    raise
        return asset_map

    @staticmethod
    def _try_append_wrapper_to_list(
        albums_list: list[AlbumResponseWrapper],
        wrapper: AlbumResponseWrapper,
        client: ImmichClient | None = None,
        tag_mod_report: ModificationReport | None = None,
    ) -> None:
        """Central helper: attempt to append a wrapper to an albums list with duplicate handling.

        If a duplicate name exists and it's a temporary album, attempt to delete the duplicate on
        the server (if `client` is provided) and skip adding. If it's a non-temporary duplicate,
        raise RuntimeError. This centralizes duplicate detection used during initial load and
        during runtime album creation.
        """
        name = wrapper.get_album_name()
        # Check existing names
        for existing in albums_list:
            try:
                if existing.get_album_name() == name:
                    # Duplicate detected
                    try:
                        if is_temporary_album(name) and client is not None:
                            from uuid import UUID
                            from immich_client.api.albums.delete_album import (
                                sync_detailed as delete_album_sync,
                            )

                            try:
                                # Attempt to delete the duplicate temporary album on the server.
                                delete_album_sync(id=UUID(wrapper.get_album_id()), client=client)
                                # Log deletion and record modification if available
                                from immich_autotag.logging.levels import LogLevel
                                from immich_autotag.logging.utils import log

                                log(
                                    f"Temporary duplicate album '{name}' (id={wrapper.get_album_id()}) deleted during add.",
                                    level=LogLevel.FOCUS,
                                )
                                if tag_mod_report is not None:
                                    try:
                                        from immich_autotag.tags.modification_kind import ModificationKind

                                        tag_mod_report.add_album_modification(
                                            kind=ModificationKind.DELETE_ALBUM,
                                            album=AlbumResponseWrapper.from_partial_dto(
                                                wrapper._active_dto()
                                            ),
                                            old_value=name,
                                            extra={
                                                "reason": "Removed duplicate temporary album during add"
                                            },
                                        )
                                    except Exception:
                                        pass
                                # Skip adding this wrapper
                                return
                            except Exception:
                                # Deletion failed: log and skip to avoid aborting startup
                                from immich_autotag.logging.levels import LogLevel
                                from immich_autotag.logging.utils import log

                                log(
                                    f"Failed to delete temporary duplicate album '{name}' (id={wrapper.get_album_id()}) during add. Skipping.",
                                    level=LogLevel.WARNING,
                                )
                                return
                        # Not temporary or no client: cannot resolve automatically
                        raise RuntimeError(
                            f"Duplicate album name detected when adding album: {name!r}"
                        )
                    except RuntimeError:
                        raise
                    except Exception:
                        # Any other error: treat as fatal duplicate
                        raise RuntimeError(
                            f"Duplicate album name detected when adding album: {name!r}"
                        )
            except Exception:
                # If existing wrapper misbehaves, fail fast
                raise
        # No duplicate: append
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
        # Check for existing album with same name
        for existing in list(self.albums):
            try:
                if existing.get_album_name() == name:
                    # Duplicate found
                    try:
                        if is_temporary_album(name) and client is not None:
                            from uuid import UUID
                            from immich_client.api.albums.delete_album import (
                                sync_detailed as delete_album_sync,
                            )

                            try:
                                delete_album_sync(id=UUID(existing.get_album_id()), client=client)
                                # Remove from local collection
                                self._remove_album_from_local_collection(existing)
                                from immich_autotag.logging.levels import LogLevel
                                from immich_autotag.logging.utils import log

                                log(
                                    f"Temporary duplicate album '{name}' (id={existing.get_album_id()}) deleted during add and removed from local collection.",
                                    level=LogLevel.FOCUS,
                                )
                                if tag_mod_report is not None:
                                    try:
                                        from immich_autotag.tags.modification_kind import ModificationKind

                                        tag_mod_report.add_album_modification(
                                            kind=ModificationKind.DELETE_ALBUM,
                                            album=existing,
                                            old_value=name,
                                            extra={"reason": "Removed duplicate temporary album during add"},
                                        )
                                    except Exception:
                                        pass
                                break
                            except Exception:
                                # Deletion failed: log and skip deletion, but do not abort
                                from immich_autotag.logging.levels import LogLevel
                                from immich_autotag.logging.utils import log

                                log(
                                    f"Failed to delete temporary duplicate album '{name}' (id={existing.get_album_id()}) during add. Skipping deletion.",
                                    level=LogLevel.WARNING,
                                )
                                # Attempt to continue by removing locally to avoid failing startup
                                try:
                                    self._remove_album_from_local_collection(existing)
                                except Exception:
                                    pass
                                break
                        # Not temporary or no client: cannot resolve automatically
                        raise RuntimeError(f"Duplicate album name detected when adding album: {name!r}")
                    except RuntimeError:
                        raise
                    except Exception:
                        raise RuntimeError(f"Duplicate album name detected when adding album: {name!r}")
            except Exception:
                # If existing wrapper misbehaves, fail fast
                raise

        # Append to collection and update maps
        self.albums.append(wrapper)
        try:
            self._add_album_to_map(wrapper)
        except Exception:
            pass
        return wrapper

    @conditional_typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[AlbumResponseWrapper]:
        """Returns the AlbumResponseWrapper objects for all albums the asset belongs to (O(1) lookup via map)."""
        return list(self._asset_to_albums_map.get(asset.id, AlbumList()))

    @conditional_typechecked
    def album_names_for_asset(self, asset: AssetResponseDto) -> list[str]:
        """Returns the names of the albums the asset belongs to.
        Use this only if you need names (e.g., for logging). Prefer albums_for_asset() for object access.
        """
        return [w.get_album_name() for w in self.albums_for_asset(asset)]

    @conditional_typechecked
    def albums_for_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> list[AlbumResponseWrapper]:
        """Returns the AlbumResponseWrapper objects for all albums the asset (wrapped) belongs to."""
        return self.albums_for_asset(asset_wrapper.asset)

    @conditional_typechecked
    def albums_wrappers_for_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> list[AlbumResponseWrapper]:
        """Returns the AlbumResponseWrapper objects for all albums the asset (wrapped) belongs to.
        This is now redundant with albums_for_asset_wrapper() but kept for compatibility.
        This method is more explicit about returning wrapper objects."""
        return self.albums_for_asset_wrapper(asset_wrapper)

    @typechecked
    def remove_album(
        self, album_wrapper: AlbumResponseWrapper, client: ImmichClient
    ) -> bool:
        """
        Elimina un álbum tanto en el servidor como de la colección interna.
        Devuelve True si se eliminó correctamente, False si no estaba en la colección.
        Lanza excepción si la API falla.
        """
        from uuid import UUID

        from immich_client.api.albums.delete_album import (
            sync_detailed as delete_album_sync,
        )

        album_id = UUID(album_wrapper.get_album_id())
        delete_album_sync(id=album_id, client=client)
        self._remove_album_from_local_collection(album_wrapper)
        # Log DELETE_ALBUM event
        from immich_autotag.report.modification_report import ModificationReport
        from immich_autotag.tags.modification_kind import ModificationKind

        tag_mod_report = ModificationReport.get_instance()
        tag_mod_report.add_album_modification(
            kind=ModificationKind.DELETE_ALBUM,
            album=album_wrapper,
        )
        return True

    @conditional_typechecked
    def create_or_get_album_with_user(
        self,
        album_name: str,
        client: ImmichClient,
        tag_mod_report: ModificationReport | None = None,
    ) -> "AlbumResponseWrapper":
        """
        Searches for an album by name. If it does not exist, creates it and assigns the current user as EDITOR.
        Updates the internal collection if created.
        """
        # Search for existing album; if a duplicate name exists and it's a
        # temporary album, attempt to delete it on the server and remove it
        # locally so we can proceed to create a fresh album. Otherwise fail-fast.
        for album_wrapper in list(self.albums):
            try:
                if album_wrapper.get_album_name() == album_name:
                    try:
                        if is_temporary_album(album_name):
                            from uuid import UUID
                            from immich_client.api.albums.delete_album import (
                                sync_detailed as delete_album_sync,
                            )
                            try:
                                delete_album_sync(id=UUID(album_wrapper.get_album_id()), client=client)
                                # Remove locally
                                self._remove_album_from_local_collection(album_wrapper)
                                from immich_autotag.logging.levels import LogLevel
                                from immich_autotag.logging.utils import log
                                log(
                                    f"Temporary duplicate album '{album_name}' (id={album_wrapper.get_album_id()}) deleted during create_or_get_album_with_user.",
                                    level=LogLevel.FOCUS,
                                )
                                if tag_mod_report is not None:
                                    try:
                                        from immich_autotag.tags.modification_kind import ModificationKind
                                        tag_mod_report.add_album_modification(
                                            kind=ModificationKind.DELETE_ALBUM,
                                            album=album_wrapper,
                                            old_value=album_name,
                                            extra={"reason": "Removed duplicate temporary album during create"},
                                        )
                                    except Exception:
                                        pass
                                # continue to creation
                                break
                            except Exception:
                                # If deletion fails, log a warning and skip removal to avoid aborting
                                from immich_autotag.logging.levels import LogLevel
                                from immich_autotag.logging.utils import log
                                log(
                                    f"Failed to delete temporary duplicate album '{album_name}' (id={album_wrapper.get_album_id()}) during create: continuing without deletion.",
                                    level=LogLevel.WARNING,
                                )
                                # Try to proceed by removing local reference if possible
                                try:
                                    self._remove_album_from_local_collection(album_wrapper)
                                except Exception:
                                    pass
                                break
                        # Not temporary: fail fast
                        raise RuntimeError(
                            f"Attempt to create album with duplicate name: {album_name!r}"
                        )
                    except RuntimeError:
                        raise
                    except Exception:
                        raise RuntimeError(
                            f"Attempt to create album with duplicate name: {album_name!r}"
                        )
            except Exception:
                # If a wrapper misbehaves, fail fast
                raise

        # If it does not exist, create and assign user
        from uuid import UUID

        from immich_client.api.albums import add_users_to_album, create_album
        from immich_client.api.users import get_my_user
        from immich_client.models.add_users_dto import AddUsersDto
        from immich_client.models.album_user_add_dto import AlbumUserAddDto
        from immich_client.models.album_user_role import AlbumUserRole
        from immich_client.models.create_album_dto import CreateAlbumDto

        # (import removed, already imported at module level)

        album = create_album.sync(
            client=client, body=CreateAlbumDto(album_name=album_name)
        )
        if album is None:
            raise RuntimeError("Failed to create album: API returned None")
        user = get_my_user.sync(client=client)
        if user is None:
            raise RuntimeError("Failed to get current user: API returned None")
        user_id = UUID(user.id)
        # Avoid adding the owner as editor (Immich API returns error 400 if attempted)
        # We assume that album.owner_id is the owner's id
        owner_id = UUID(album.owner_id)
        if user_id == owner_id:
            pass  # Do not add the owner as editor
        else:
            try:
                add_users_to_album.sync(
                    id=UUID(album.id),
                    client=client,
                    body=AddUsersDto(
                        album_users=[
                            AlbumUserAddDto(user_id=user_id, role=AlbumUserRole.EDITOR)
                        ]
                    ),
                )
            except Exception as e:
                raise RuntimeError(
                    f"Error adding user {user_id} as EDITOR to album {album.id} ('{album.album_name}'): {e}"
                ) from e
        wrapper = AlbumResponseWrapper.from_partial_dto(album)
        # Add with centralized duplicate handling
        try:
            wrapper = self.add_album_wrapper(wrapper, client=client, tag_mod_report=tag_mod_report)
        except Exception:
            # If uniqueness fails, raise - fail-fast as requested
            raise
        if tag_mod_report:
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report.add_album_modification(
                kind=ModificationKind.CREATE_ALBUM,
                album=wrapper,
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

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log("Albums:", level=LogLevel.INFO)
        seen_names: set[str] = set()
        for album in albums:
            # Create wrapper with partial album data (no assets fetched yet)
            # Assets will be fetched lazily when needed
            wrapper = AlbumResponseWrapper.from_partial_dto(album)
            # Use centralized helper to attempt append with duplicate handling
            try:
                AlbumCollectionWrapper._try_append_wrapper_to_list(
                    albums_wrapped, wrapper, client=client, tag_mod_report=tag_mod_report
                )
            except RuntimeError:
                raise
            log(
                f"- {wrapper.get_album_name()} (assets: lazy-loaded)",
                level=LogLevel.DEBUG,
            )

        tag_mod_report.flush()
        log(f"Total albums: {len(albums_wrapped)}", level=LogLevel.INFO)
        MIN_ALBUMS = 326
        if len(albums_wrapped) < MIN_ALBUMS:
            raise Exception(
                f"ERROR: Unexpectedly low number of albums: {len(albums_wrapped)} < {MIN_ALBUMS}"
            )
        return cls(albums=AlbumList(albums_wrapped))
