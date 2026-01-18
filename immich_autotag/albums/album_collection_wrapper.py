from __future__ import annotations

from functools import cached_property

import attrs
from immich_client.models.asset_response_dto import AssetResponseDto

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper

# Import for type checking and runtime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient
from immich_autotag.utils.decorators import conditional_typechecked



# Singleton instance storage
_album_collection_singleton: AlbumCollectionWrapper | None = None

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumCollectionWrapper:
    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    def __attrs_post_init__(self):
        global _album_collection_singleton
        if _album_collection_singleton is not None:
            raise RuntimeError("AlbumCollectionWrapper is a singleton: only one instance is allowed.")
        _album_collection_singleton = self

    @classmethod
    def get_instance(cls) -> "AlbumCollectionWrapper":
        global _album_collection_singleton
        if _album_collection_singleton is None:
            raise RuntimeError("AlbumCollectionWrapper singleton has not been initialized yet.")
        return _album_collection_singleton

    @cached_property
    def _asset_to_albums_map(self) -> dict[str, list[AlbumResponseWrapper]]:
        """Pre-computed map: asset_id -> list of AlbumResponseWrapper objects (O(1) lookup).

        Antes de construir el mapa, fuerza la carga de asset_ids en todos los álbumes (lazy loading).
        """
        asset_map: dict[str, list[AlbumResponseWrapper]] = {}
        assert len(self.albums) > 0, "AlbumCollectionWrapper must have at least one album to build asset map."
        for album_wrapper in self.albums:
            # Forzar la recarga de assets si asset_ids está vacío
            if not album_wrapper.asset_ids:
                # Recarga desde la API y actualiza el cache
                # Necesita un ImmichClient, aquí asumimos que el wrapper tiene acceso o se debe pasar
                # Si no tienes el cliente, puedes modificar para pasarlo como argumento
                from immich_autotag.config.internal_config import get_default_client
                client = get_default_client()
                album_wrapper.reload_from_api(client)
                if not album_wrapper.asset_ids:
                    print(f"[WARN] Album '{getattr(album_wrapper.album, 'album_name', '?')}' has no assets after forced reload.")
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
        from immich_client.models.album_response_dto import AlbumResponseDto
        from immich_client.models.album_user_add_dto import AlbumUserAddDto
        from immich_client.models.album_user_role import AlbumUserRole
        from immich_client.models.create_album_dto import CreateAlbumDto

        # (import removed, already imported at module level)

        album = create_album.sync(
            client=client, body=CreateAlbumDto(album_name=album_name)
        )
        user = get_my_user.sync(client=client)
        user_id = user.id
        # Avoid adding the owner as editor (Immich API returns error 400 if attempted)
        # We assume that album.owner_id is the owner's id
        if user_id == album.owner_id:
            pass  # Do not add the owner as editor
        else:
            try:
                add_users_to_album.sync(
                    id=album.id,
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
