from typing import Any

from immich_client.api.albums import update_album_user
from immich_client.client import AuthenticatedClient
from immich_client.models.album_user_role import AlbumUserRole
from immich_client.models.update_album_user_dto import UpdateAlbumUserDto
from immich_client.types import Response

from immich_autotag.api.immich_proxy.debug import write_operation_debug
from immich_autotag.types.uuid_wrappers import AlbumUUID, UserUUID


def proxy_update_album_user(
    *,
    client: AuthenticatedClient,
    album_id: AlbumUUID,
    user_id: UserUUID,
    role: AlbumUserRole,
) -> Response[Any]:
    write_operation_debug()
    body = UpdateAlbumUserDto(role=role)
    return update_album_user.sync_detailed(
        client=client, id=album_id.to_uuid(), user_id=str(user_id), body=body
    )


__all__ = ["proxy_update_album_user"]
