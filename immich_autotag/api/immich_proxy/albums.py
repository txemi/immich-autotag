
from typing import  List
from uuid import UUID

from immich_client import Client
from immich_client.api.albums import (
    add_assets_to_album,
    get_album_info,
    get_all_albums,
    remove_asset_from_album,
    update_album_info,
)
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto
from immich_client.models.update_album_dto import UpdateAlbumDto

from immich_client.models.add_users_dto import AddUsersDto


def proxy_get_album_info(*, album_id: UUID, client: Client) -> AlbumResponseDto:
    return get_album_info.sync(id=album_id, client=client)

def proxy_get_all_albums(*, client: Client) -> list[AlbumResponseDto]:
    return get_all_albums.sync(client=client)

def proxy_add_assets_to_album(*, album_id: UUID, client: Client, asset_ids: List[UUID]) -> list[BulkIdResponseDto]:
    return add_assets_to_album.sync(id=album_id, client=client, body=BulkIdsDto(ids=asset_ids))

def proxy_remove_asset_from_album(*, album_id: UUID, client: Client, asset_ids: List[UUID]) -> list[BulkIdResponseDto]:
    return remove_asset_from_album.sync(id=album_id, client=client, body=BulkIdsDto(ids=asset_ids))

def proxy_update_album_info(*, album_id: UUID, client: Client, body: UpdateAlbumDto) -> AlbumResponseDto:
    return update_album_info.sync(id=album_id, client=client, body=body)



def proxy_add_users_to_album(
    *, album_id: UUID, client: Client, body: AddUsersDto
) -> AlbumResponseDto:
    from immich_client.api.albums import add_users_to_album

    return add_users_to_album.sync(id=album_id, client=client, body=body)



def proxy_get_all_albums(*, client: Client) -> AlbumResponseDto:
    return get_all_albums.sync(client=client)


def proxy_add_assets_to_album(
    *, album_id: UUID, client: Client, asset_ids: List[UUID]
) -> list[BulkIdResponseDto]:
    return add_assets_to_album.sync(
        id=album_id, client=client, body=BulkIdsDto(ids=asset_ids)
    )


