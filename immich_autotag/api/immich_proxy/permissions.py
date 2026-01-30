import uuid
from typing import Any

from immich_client.api.albums import remove_user_from_album
from immich_client.api.users import search_users
from immich_client.client import AuthenticatedClient
from immich_client.models.user_response_dto import UserResponseDto
from immich_client.types import Response

from immich_autotag.types.uuid_wrappers import UserUUID


def proxy_search_users(*, client: AuthenticatedClient) -> list[UserResponseDto]:
    result = search_users.sync(client=client)
    if result is None:
        return []
    return result


def proxy_remove_user_from_album(
    *, client: AuthenticatedClient, album_id: AlbumUUID, user_id: UserUUID
) -> Response[Any]:
    return remove_user_from_album.sync_detailed(
        client=client, id=album_id, user_id=str(user_id)
    )
