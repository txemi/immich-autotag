
from immich_client.client import AuthenticatedClient
from immich_client.models.user_admin_response_dto import UserAdminResponseDto
from typeguard import typechecked

from immich_autotag.api.immich_proxy.users import proxy_get_my_user


@typechecked
def get_current_user(context: AuthenticatedClient) -> UserAdminResponseDto:
    """
    Returns the current user using the Immich context client.
    Returns the complete user object (you can access .id, .email, .name, etc.).
    """
    return proxy_get_my_user(client=context)
