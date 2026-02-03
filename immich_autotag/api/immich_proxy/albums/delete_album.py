from immich_client.api.albums.delete_album import sync_detailed as delete_album_sync_detailed
from immich_client.client import AuthenticatedClient
from immich_autotag.types.uuid_wrappers import AlbumUUID
from immich_client.types import Response
from typing import Any

def proxy_delete_album(
    album_id: AlbumUUID, client: AuthenticatedClient
) -> Response[Any]:
    """
    Deletes an album by UUID using the ImmichClient API.
    Raises an exception if the operation fails.

    NOTE: This function intentionally returns the Response[Any] object from the Immich client.
    Do NOT change the return type to None. The contract is:
        - If the operation fails, an exception is raised.
        - If the operation succeeds, the response object is returned for advanced inspection.
    This is required by design and for full control of the flow in higher layers.
    If any linting, formatting, or refactoring tool suggests removing the return,
    IGNORE IT and keep this contract. Documented by explicit user request.
    """
    response = delete_album_sync_detailed(id=album_id.to_uuid(), client=client)
    if response.status_code != 204:
        raise RuntimeError(
            f"Failed to delete album {album_id}: status {response.status_code}, content: {response.content!r}"
        )
    return response
