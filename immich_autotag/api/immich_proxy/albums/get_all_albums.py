from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.client import AuthenticatedClient
from immich_client.api.albums import get_all_albums

def proxy_get_all_albums(*, client: AuthenticatedClient) -> list[AlbumResponseDto]:
    result = get_all_albums.sync(client=client)
    if result is None:
        raise RuntimeError("Failed to fetch albums: API returned None")
    return result
