from typing import Any

from immich_client.api.users import get_my_user
from typeguard import typechecked


@typechecked
def get_current_user(context: Any) -> Any:
    """
    Returns the current user using the Immich context client.
    Returns the complete user object (you can access .id, .email, .name, etc.).
    """
    return get_my_user.sync(client=context.client)
