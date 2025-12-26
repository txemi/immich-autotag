
from __future__ import annotations

import attrs
from typeguard import typechecked

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_client.models.asset_response_dto import AssetResponseDto


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumCollectionWrapper:
    albums: list[AlbumResponseWrapper] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    @typechecked
    def albums_for_asset(self, asset: AssetResponseDto) -> list[str]:
        """Returns the names of the albums the asset belongs to."""
        album_names = []
        for album_wrapper in self.albums:
            if album_wrapper.has_asset(asset):
                album_names.append(album_wrapper.album.album_name)
        return album_names
    @typechecked
    def create_or_get_album_with_user(self, album_name: str, client, tag_mod_report=None) -> AlbumResponseWrapper:
        """
        Searches for an album by name. If it does not exist, creates it and assigns the current user as EDITOR.
        Updates the internal collection if created.
        """
        # Search for existing album
        for album_wrapper in self.albums:
            if album_wrapper.album.album_name == album_name:
                return album_wrapper

        # If it does not exist, create and assign user
        from immich_client.api.albums import create_album, add_users_to_album
        from immich_client.api.users import get_my_user
        from immich_client.models.add_users_dto import AddUsersDto
        from immich_client.models.album_user_add_dto import AlbumUserAddDto
        from immich_client.models.album_user_role import AlbumUserRole
        from immich_client.models.album_response_dto import AlbumResponseDto
        from immich_client.models.album_create_dto import AlbumCreateDto
        from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper

        album = create_album.sync(client=client, body=AlbumCreateDto(album_name=album_name))
        user = get_my_user.sync(client=client)
        user_id = user.id
        add_users_to_album.sync(
            id=album.id,
            client=client,
            body=AddUsersDto(album_users=[AlbumUserAddDto(user_id=user_id, role=AlbumUserRole.EDITOR)])
        )
        wrapper = AlbumResponseWrapper(album=album)
        # Update internal collection (since it's frozen, must rebuild)
        self.albums.append(wrapper)
        if tag_mod_report:
            tag_mod_report.add_album_modification(
                action="create",
                album_id=album.id,
                album_name=album_name,
            )
        return wrapper