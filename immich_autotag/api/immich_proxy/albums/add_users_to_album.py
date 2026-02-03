from immich_client.api.albums import add_users_to_album
from immich_client.client import AuthenticatedClient
from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_response_dto import AlbumResponseDto

from immich_autotag.types.uuid_wrappers import AlbumUUID


def proxy_add_users_to_album(
    *, album_id: AlbumUUID, client: AuthenticatedClient, body: AddUsersDto
) -> AlbumResponseDto:
    result = add_users_to_album.sync(id=album_id.to_uuid(), client=client, body=body)
    if result is None:
        raise RuntimeError("Failed to add users to album")
    return result
