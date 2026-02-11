from typing import Any

from immich_client.api.albums import remove_user_from_album
from immich_client.client import AuthenticatedClient
from immich_client.types import Response

from immich_autotag.api.immich_proxy.debug import write_operation_debug
from immich_autotag.types.uuid_wrappers import AlbumUUID, UserUUID


def proxy_remove_user_from_album(
    *, client: AuthenticatedClient, album_id: AlbumUUID, user_id: UserUUID
) -> Response[Any]:
    write_operation_debug()
    return remove_user_from_album.sync_detailed(
        client=client, id=album_id.to_uuid(), user_id=str(user_id)
    )


__all__ = ["proxy_remove_user_from_album"]
