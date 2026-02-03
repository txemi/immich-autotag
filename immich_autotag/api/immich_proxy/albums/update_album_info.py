from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.update_album_dto import UpdateAlbumDto
from immich_client.client import AuthenticatedClient
from immich_autotag.types.uuid_wrappers import AlbumUUID
from immich_client.api.albums import update_album_info

def proxy_update_album_info(
    *, album_id: AlbumUUID, client: AuthenticatedClient, body: UpdateAlbumDto
) -> AlbumResponseDto:
    result = update_album_info.sync(id=album_id.to_uuid(), client=client, body=body)
    if result is None:
        raise RuntimeError("Failed to update album info")
    return result
