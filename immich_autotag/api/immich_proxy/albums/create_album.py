from immich_client.client import AuthenticatedClient
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.create_album_dto import CreateAlbumDto


def proxy_create_album(
    *, client: AuthenticatedClient, body: CreateAlbumDto
) -> AlbumResponseDto:
    """
    Calls the Immich API to create an album and returns the AlbumResponseDto.
    """
    from immich_client.api.albums.create_album import sync as create_album_sync

    result = create_album_sync(client=client, body=body)
    if result is None:
        raise RuntimeError("Failed to create album: API returned None.")
    return result
