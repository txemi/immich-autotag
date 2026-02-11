from immich_client.api.albums import remove_asset_from_album
from immich_client.client import AuthenticatedClient
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto

from immich_autotag.api.immich_proxy.debug import write_operation_debug
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID


def proxy_remove_asset_from_album(
    *, album_id: AlbumUUID, client: AuthenticatedClient, asset_ids: list[AssetUUID]
) -> list[BulkIdResponseDto]:

    write_operation_debug()
    uuid_ids = [a.to_uuid() for a in asset_ids]
    result = remove_asset_from_album.sync(
        id=album_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
    )
    if result is None:
        raise RuntimeError(
            f"Failed to remove assets from album {album_id}: API returned None"
        )
    return result
