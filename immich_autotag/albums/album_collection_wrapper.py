from __future__ import annotations

from functools import cached_property

import attrs
from immich_client.models.asset_response_dto import AssetResponseDto
from typeguard import typechecked

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.album_list import AlbumList
from immich_autotag.albums.asset_to_albums_map import AssetToAlbumsMap
from immich_autotag.assets.albums.temporary_albums import is_temporary_album

# Import for type checking and runtime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient
from immich_autotag.utils.decorators import conditional_typechecked

# Singleton instance storage
_album_collection_singleton: AlbumCollectionWrapper | None = None


@attrs.define(auto_attribs=True, slots=True)

class AlbumCollectionWrapper:


    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )
    _asset_to_albums_map: AssetToAlbumsMap = attrs.field(
        init=False,
        factory=AssetToAlbumsMap,
        validator=attrs.validators.instance_of(AssetToAlbumsMap)
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

        self._asset_to_albums_map = self._asset_to_albums_map()

    @typechecked
    def _add_album_to_map(self, album_wrapper: AlbumResponseWrapper):
        for asset_id in album_wrapper.asset_ids:
            if asset_id not in self._asset_to_albums_map:
                self._asset_to_albums_map[asset_id] = AlbumList()
            self._asset_to_albums_map[asset_id].append(album_wrapper)

    @typechecked
    def _remove_album_from_map(self, album_wrapper: AlbumResponseWrapper):
        for asset_id in album_wrapper.asset_ids:
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
                f"[ALBUM REMOVAL] Album {album_wrapper.album.id} ('{album_wrapper.album.album_name}') removed from collection (local, not_found cleanup).",
                level=LogLevel.FOCUS,
            )
        return removed

    @typechecked
    def _asset_to_albums_map(self) -> AssetToAlbumsMap:
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
            if not album_wrapper.asset_ids:
                print(
                    f"[WARN] Album '{album_wrapper.album.album_name}' has no assets after forced reload."
                )
                # album_wrapper.reload_from_api(client)
                if album_wrapper.asset_ids:
                    album_url = album_wrapper.get_immich_album_url().geturl()
                    raise RuntimeError(
                        f"[DEBUG] Anomalous behavior: Album '{album_wrapper.album.album_name}' (URL: {album_url}) had empty asset_ids after initial load, but after a redundant reload it now has assets. "
                        "This suggests a possible synchronization or lazy loading bug. Please review the album loading logic."
                    )
                if is_temporary_album(album_wrapper.album.album_name):
                    print(
                        f"[WARN] Temporary album '{album_wrapper.album.album_name}' marked for removal after map build."
                    )
                    albums_to_remove.append(album_wrapper)
                pass
            else:
                print(
                    f"[INFO] Album '{album_wrapper.album.album_name}' reloaded with {len(album_wrapper.asset_ids)} assets."
                )

            for asset_id in album_wrapper.asset_ids:
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
                            old_value=album_wrapper.album.album_name,
                            extra={
                                "reason": "Removed automatically after map build because it was empty and temporary"
                            },
                        )
                    self.remove_album(album_wrapper, client)
                except Exception as e:
                    album = album_wrapper.album  # type: ignore
                    album_name = album.album_name
                    print(
                        f"[ERROR] Failed to remove temporary album '{album_name}': {e}"
                    )
                    raise
        return asset_map

    @conditional_typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[AlbumResponseWrapper]:
        """Returns the AlbumResponseWrapper objects for all albums the asset belongs to (O(1) lookup via map)."""
        return list(self._asset_to_albums_map.get(asset.id, AlbumList()))

    @conditional_typechecked
    def album_names_for_asset(self, asset: AssetResponseDto) -> list[str]:
        """Returns the names of the albums the asset belongs to.
        Use this only if you need names (e.g., for logging). Prefer albums_for_asset() for object access.
        """
        return [w.album.album_name for w in self.albums_for_asset(asset)]

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
        album_id = UUID(album_wrapper.album.id)
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
        # Search for existing album
        for album_wrapper in self.albums:
            if album_wrapper.album.album_name == album_name:
                return album_wrapper

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
        wrapper = AlbumResponseWrapper(album_partial=album)
        # Update internal collection (since it's frozen, must rebuild)
        self.albums.append(wrapper)
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

        print("\nAlbums:")
        for album in albums:
            # Create wrapper with partial album data (no assets fetched yet)
            # Assets will be fetched lazily when needed
            wrapper = AlbumResponseWrapper(album_partial=album)
            print(f"- {wrapper.album.album_name} (assets: lazy-loaded)")
            albums_wrapped.append(wrapper)

        tag_mod_report.flush()
        print(f"Total albums: {len(albums_wrapped)}\n")
        MIN_ALBUMS = 326
        if len(albums_wrapped) < MIN_ALBUMS:
            raise Exception(
                f"ERROR: Unexpectedly low number of albums: {len(albums_wrapped)} < {MIN_ALBUMS}"
            )
        return cls(albums=albums_wrapped)
