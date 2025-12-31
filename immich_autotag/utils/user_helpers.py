from immich_client.api.users import get_my_user
from typeguard import typechecked
from typing import Any



@typechecked
def get_current_user(context: Any) -> Any:
    """
    Devuelve el usuario actual usando el cliente del contexto Immich.
    Retorna el objeto usuario completo (puedes acceder a .id, .email, .name, etc.).
    """
    return get_my_user.sync(client=context.client)
