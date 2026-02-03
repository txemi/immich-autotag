from immich_client.api.users import search_users
from immich_client.client import AuthenticatedClient
from immich_client.models.user_response_dto import UserResponseDto


def proxy_search_users(*, client: AuthenticatedClient) -> list[UserResponseDto]:
    result = search_users.sync(client=client)
    if result is None:
        return []
    return result
