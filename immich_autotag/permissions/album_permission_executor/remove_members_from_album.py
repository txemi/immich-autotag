from typing import Sequence
from uuid import UUID
from typeguard import typechecked
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.api.immich_proxy.permissions import proxy_remove_user_from_album
from immich_autotag.logging.utils import log_debug

if True:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

@typechecked
def _remove_members_from_album(*, album: 'AlbumResponseWrapper', user_ids: Sequence[str], context: ImmichContext) -> None:
    """
    Remove users from album using the API. Logs each removal.
    """
    album_id = album.get_album_uuid()
    album_name = album.get_album_name()
    client = context.get_client_wrapper().get_client()
    for user_id in user_ids:
        proxy_remove_user_from_album(client=client, album_id=album_id, user_id=UUID(user_id))
        log_debug(f"[ALBUM_PERMISSIONS] Removed user {user_id} from {album_name}")
