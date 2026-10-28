from __future__ import annotations

from immich_client.api.search.search_assets import sync as search_assets
from immich_client.client import AuthenticatedClient
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.metadata_search_dto import MetadataSearchDto

from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID

# Largest page the search endpoint accepts.
_PAGE_SIZE = 1000


def proxy_get_album_assets(
    *, album_id: AlbumUUID, client: AuthenticatedClient
) -> list[AssetResponseDto]:
    """
    Returns every asset of an album, as full AssetResponseDto.

    Since Immich v3 the album DTO no longer embeds its assets: the official
    replacement is POST /search/metadata filtered by albumIds. No visibility
    filter is sent, so archived and hidden assets of the album are included,
    like the old embedded list. Works the same against v2 servers.
    """
    result: list[AssetResponseDto] = []
    page = 1
    while True:
        body = MetadataSearchDto(
            album_ids=[album_id.to_uuid()], page=page, size=_PAGE_SIZE
        )
        response = search_assets(client=client, body=body)
        if response is None:
            raise RuntimeError(
                f"Search for the assets of album {album_id} returned no response "
                f"(page {page})."
            )
        result.extend(response.assets.items)
        if not response.assets.next_page:
            return result
        page += 1


def proxy_get_album_asset_uuids(
    *, album_id: AlbumUUID, client: AuthenticatedClient
) -> set[AssetUUID]:
    """Returns the UUIDs of every asset of an album (see proxy_get_album_assets)."""
    return {
        AssetUUID(asset.id)
        for asset in proxy_get_album_assets(album_id=album_id, client=client)
    }


def proxy_is_asset_in_album(
    *, album_id: AlbumUUID, asset_id: AssetUUID, client: AuthenticatedClient
) -> bool:
    """Whether one asset belongs to an album, without listing the whole album."""
    body = MetadataSearchDto(
        album_ids=[album_id.to_uuid()], id=asset_id.to_uuid(), size=1
    )
    response = search_assets(client=client, body=body)
    if response is None:
        raise RuntimeError(
            f"Search for asset {asset_id} in album {album_id} returned no response."
        )
    return len(response.assets.items) > 0
