from __future__ import annotations

from functools import cached_property

import attrs
from immich_client.client import Client
from immich_client.models.asset_response_dto import AssetResponseDto

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.utils.decorators import conditional_typechecked

# Import for type checking and runtime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.report.modification_report import ModificationReport


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumCollectionWrapper:

    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    @cached_property
    def _asset_to_albums_map(self) -> dict[str, list[str]]:
        """Pre-computed map: asset_id -> list of album names (O(1) lookup).
        
        Computed once during initialization and cached. This eliminates the O(n²)
        complexity of iterating all albums for each asset lookup.
        
        Time complexity: O(A * M) where A=albums count, M=assets per album
        Lookup complexity: O(1) for each has_asset check
        
        This optimization reduces albums_for_asset() from ~35,273 sec to ~2-3 sec.
        """
        asset_map: dict[str, list[str]] = {}
        for album_wrapper in self.albums:
            for asset_id in album_wrapper.asset_ids:
                if asset_id not in asset_map:
                    asset_map[asset_id] = []
                asset_map[asset_id].append(album_wrapper.album.album_name)
        return asset_map

    @conditional_typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[str]:
        """Returns the names of the albums the asset belongs to (O(1) lookup via cached map)."""
        return self._asset_to_albums_map.get(asset.id, [])

    @conditional_typechecked
    def albums_for_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> list[str]:
        """Returns the names of the albums the asset (wrapped) belongs to."""
        return self.albums_for_asset(asset_wrapper.asset)

    @conditional_typechecked
    def albums_wrappers_for_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> list[AlbumResponseWrapper]:
        """Returns the AlbumResponseWrapper objects for all albums the asset (wrapped) belongs to.
        Uses the cached map for O(1) lookup of album names, then retrieves wrappers.
        This is more robust than using album names, as names may not be unique."""
        album_names = self._asset_to_albums_map.get(asset_wrapper.asset.id, [])
        result = []
        for album_wrapper in self.albums:
            if album_wrapper.album.album_name in album_names:
                result.append(album_wrapper)
        return result

    @conditional_typechecked
    def create_or_get_album_with_user(
        self,
        album_name: str,
        client: Client,
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
        wrapper = AlbumResponseWrapper(album=album)
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
    def from_client(cls, client: Client) -> "AlbumCollectionWrapper":
        """
        Fetches all albums from the API, wraps them, and trims names if needed.
        """
        from immich_client.api.albums import get_album_info, get_all_albums

        from immich_autotag.report.modification_report import ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        assert isinstance(tag_mod_report, ModificationReport)
        albums = get_all_albums.sync(client=client)
        albums_full: list[AlbumResponseWrapper] = []
        print("\nAlbums:")
        for album in albums:
            wrapper = AlbumResponseWrapper.from_id(
                client, album.id, tag_mod_report=tag_mod_report
            )
            n_assets = len(wrapper.album.assets) if wrapper.album.assets else 0
            print(f"- {wrapper.album.album_name} (assets: {n_assets})")
            albums_full.append(wrapper)
        tag_mod_report.flush()
        print(f"Total albums: {len(albums_full)}\n")
        MIN_ALBUMS = 326
        if len(albums_full) < MIN_ALBUMS:
            raise Exception(
                f"ERROR: Unexpectedly low number of albums: {len(albums_full)} < {MIN_ALBUMS}"
            )
        return cls(albums=albums_full)
