from __future__ import annotations

from functools import cached_property

import attrs
from immich_client.models.asset_response_dto import AssetResponseDto
from typeguard import typechecked

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper

# Import for type checking and runtime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.albums.temporary_albums import is_temporary_album
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

    def __attrs_post_init__(self):
        global _album_collection_singleton
        if _album_collection_singleton is not None:
            raise RuntimeError(
                "AlbumCollectionWrapper is a singleton: only one instance is allowed."
            )
        _album_collection_singleton = self

    @classmethod
    def get_instance(cls) -> "AlbumCollectionWrapper":
        global _album_collection_singleton
        if _album_collection_singleton is None:
            raise RuntimeError(
                "AlbumCollectionWrapper singleton has not been initialized yet."
            )
        return _album_collection_singleton

    @cached_property
    def _asset_to_albums_map(self) -> dict[str, list[AlbumResponseWrapper]]:
        """Pre-computed map: asset_id -> list of AlbumResponseWrapper objects (O(1) lookup).

        Antes de construir el mapa, fuerza la carga de asset_ids en todos los álbumes (lazy loading).
        """
        asset_map: dict[str, list[AlbumResponseWrapper]] = {}
        assert (
            len(self.albums) > 0
        ), "AlbumCollectionWrapper must have at least one album to build asset map."
        for album_wrapper in self.albums:
            # Forzar la recarga de assets si asset_ids está vacío
            if not album_wrapper.asset_ids:
                # Recarga desde la API y actualiza el cache usando el cliente del contexto singleton
                from immich_autotag.context.immich_context import ImmichContext
                client = ImmichContext.get_default_client()
                album_wrapper.reload_from_api(client)
                if not album_wrapper.asset_ids:
                    print(
                        f"[WARN] Album '{getattr(album_wrapper.album, 'album_name', '?')}' has no assets after forced reload."
                    )
                else:
                    # Si es un álbum temporal, eliminarlo automáticamente
                    if is_temporary_album(album_wrapper.album.album_name):
                        self.remove_album(album_wrapper, client)
                    pass

            for asset_id in album_wrapper.asset_ids:
                if asset_id not in asset_map:
                    asset_map[asset_id] = []
                asset_map[asset_id].append(album_wrapper)
        return asset_map

    @conditional_typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[AlbumResponseWrapper]:
        """Returns the AlbumResponseWrapper objects for all albums the asset belongs to (O(1) lookup via cached map)."""
        return self._asset_to_albums_map.get(asset.id, [])

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
    def remove_album(self, album_wrapper: AlbumResponseWrapper, client: ImmichClient) -> bool:
        """
        Elimina un álbum tanto en el servidor como de la colección interna.
        Devuelve True si se eliminó correctamente, False si no estaba en la colección.
        Lanza excepción si la API falla.
        """
        from immich_client.api.albums.delete_album import sync_detailed as delete_album_sync
        from uuid import UUID
        # Convertir id de str a UUID antes de llamar a la API
        album_id = UUID(album_wrapper.album.id)
        # Llamada a la API para borrar el álbum en el servidor
        delete_album_sync(id=album_id, client=client)
        # Eliminar de la lista interna
        self.albums = [a for a in self.albums if a != album_wrapper]
        # Invalida el cache del mapa
        self._invalidate_asset_to_albums_map_cache()
        return True

    def _invalidate_asset_to_albums_map_cache(self):
        """Elimina el cache del mapa asset_id -> albums si existe."""
        if hasattr(self, "_asset_to_albums_map"):
            try:
                del self._asset_to_albums_map
            except Exception:
                pass

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
        from immich_client.api.albums import add_users_to_album, create_album
        from immich_client.api.users import get_my_user
        from immich_client.models.add_users_dto import AddUsersDto
        from immich_client.models.album_user_add_dto import AlbumUserAddDto
        from immich_client.models.album_user_role import AlbumUserRole
        from immich_client.models.create_album_dto import CreateAlbumDto
        from uuid import UUID

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
