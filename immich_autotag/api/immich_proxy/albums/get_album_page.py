from immich_client.api.albums import get_all_albums
from immich_client.models import AlbumResponseDto
from immich_autotag.api.immich_proxy.utils.cache_manager import ApiCacheManager, ApiCacheKey
from immich_autotag.api.immich_proxy.types import AuthenticatedClient


def proxy_get_album_page(
    *, client: AuthenticatedClient, page: int, page_size: int = 100
) -> list[AlbumResponseDto]:
    """
    Fetch a page of albums, using disk cache for each page.
    """
    cache_mgr = ApiCacheManager.create(cache_type=ApiCacheKey.ALBUM_PAGES)
    cache_key = f"page_{page}_size_{page_size}"
    cache_data = cache_mgr.load(cache_key)
    if cache_data is not None:
        # Defensive: filter only dicts
        return [
            AlbumResponseDto.from_dict(dto)
            for dto in cache_data
            if isinstance(dto, dict)
        ]
    # If not cached, fetch all albums and simulate pagination
    all_albums = get_all_albums.sync(client=client)
    if all_albums is None:
        raise RuntimeError("Failed to fetch albums: API returned None")
    # Simulate pagination
    start = (page - 1) * page_size
    end = start + page_size
    page_albums = all_albums[start:end]
    # Save to cache
    cache_mgr.save(cache_key, [dto.to_dict() for dto in page_albums])
    return page_albums
