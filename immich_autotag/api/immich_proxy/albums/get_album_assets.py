from __future__ import annotations

from immich_client.client import AuthenticatedClient

from immich_autotag.types.uuid_wrappers import AlbumUUID


def proxy_get_album_assets(
    *,
    album_id: AlbumUUID,
    client: AuthenticatedClient,
    page: int | None = None,
    size: int | None = None,
) -> list[dict]:
    """
    Fetches album assets directly from the Immich API using the underlying httpx client.

    Returns a list of raw asset dicts as returned by the API. This is intentionally
    low-level: callers should convert to DTOs or wrappers as needed.
    """
    params = {}
    if page is not None:
        params["page"] = page
    if size is not None:
        params["size"] = size

    # Use the generated client's httpx client to make a raw request to the album-assets endpoint.
    url = f"/albums/{album_id}/assets"
    resp = client.get_httpx_client().request("GET", url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # The API may return an object with `.items` or a bare list depending on server version.
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    # Fallback: return empty list for unexpected shapes
    return []
