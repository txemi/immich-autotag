
from immich_client import Client
from immich_client.api.assets import get_asset_info
from immich_client.api.albums import get_all_albums
from immich_client.models import AlbumResponseDto
from typing import List
from typeguard import typechecked

# Import configuration from the centralized module
from immich_user_config import IMMICH_HOST, IMMICH_PORT, API_KEY

IMMICH_BASE_URL = f"http://{IMMICH_HOST}:{IMMICH_PORT}/api"
PHOTO_ID = "abc02a80-ae50-4989-aebd-55263da48191"


@typechecked
def get_albums_for_asset(asset_id: str, client: Client) -> List[str]:
    """Returns the names of the albums to which an asset belongs."""
    albums = get_all_albums.sync(client=client)
    album_names = []
    for album in albums:
        asset_ids = [a.id for a in album.assets] if album.assets else []
        if asset_id in asset_ids:
            album_names.append(album.album_name)
    return album_names


@typechecked
def get_tags_for_asset(asset_id: str, client: Client) -> List[str]:
    """Returns the names of the tags associated with an asset."""
    asset = get_asset_info.sync(id=asset_id, client=client)
    return [tag.name for tag in asset.tags] if asset.tags else []


@typechecked
def main() -> None:
    client = Client(base_url=IMMICH_BASE_URL, headers={"x-api-key": API_KEY})
    print(f"Searching albums and tags for photo {PHOTO_ID}\n")
    albums = get_albums_for_asset(PHOTO_ID, client)
    tags = get_tags_for_asset(PHOTO_ID, client)
    print(f"Albums: {albums if albums else '-'}")
    print(f"Tags: {tags if tags else '-'}")

if __name__ == "__main__":
    main()
