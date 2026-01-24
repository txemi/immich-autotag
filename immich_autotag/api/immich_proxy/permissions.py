from typing import Any

from immich_client.api.albums import remove_user_from_album
from immich_client.api.users import search_users
from immich_client.client import AuthenticatedClient


def proxy_search_users(*, client: AuthenticatedClient) -> list[UserResponseDto]:
    return search_users.sync(client=client, **kwargs)


def proxy_remove_user_from_album(*, client: AuthenticatedClient) -> Any:
    return remove_user_from_album.sync(client=client, **kwargs)
