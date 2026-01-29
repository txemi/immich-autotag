from typing import List
from uuid import UUID
from typeguard import typechecked
from immich_client.models.album_user_response_dto import AlbumUserResponseDto
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.utils import log_debug

@typechecked
def _get_current_members(
    album_id: UUID, context: ImmichContext
) -> List[AlbumUserResponseDto]:
    """
    Fetch current album members from API.
    Returns list of album_user_response_dto objects with user_id attribute.
    """
    log_debug(f"[ALBUM_PERMISSIONS] Fetching current members for album {album_id}")

    from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper

    # Try to get the album wrapper from the collection first
    collection = AlbumCollectionWrapper.get_instance()
    wrapper = collection.find_album_by_id(album_id)
    album_members = wrapper.get_album_members()
    if album_members:
        log_debug(
            f"[ALBUM_PERMISSIONS] Album {album_id} (from collection) has {len(album_members)} members"
        )

    # Fallback: call API directly

    log_debug(
        f"[ALBUM_PERMISSIONS] Album {album_id} (API) has {len(album_members)} members"
    )
    return album_members
