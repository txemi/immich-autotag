from typing import Optional
from immich_client.api.users import get_my_user
from immich_client.client import AuthenticatedClient
from immich_client.models.user_admin_response_dto import UserAdminResponseDto


def proxy_get_my_user(*, client: AuthenticatedClient) -> Optional[UserAdminResponseDto]:
    return get_my_user.sync(client=client)
