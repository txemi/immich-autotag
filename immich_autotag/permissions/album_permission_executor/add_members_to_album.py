from typing import List
from uuid import UUID
from typeguard import typechecked
from immich_client.models.album_user_role import AlbumUserRole
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.add_users_dto import AddUsersDto
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.logging.levels import LogLevel
from immich_autotag.api.immich_proxy.albums import proxy_add_users_to_album
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport

if True:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper

@typechecked
def add_members_to_album(
    *,
    album: 'AlbumResponseWrapper',
    users: List['UserResponseWrapper'],
    access_level: AlbumUserRole,
    context: ImmichContext,
) -> None:
    """
    Add members to album (PONER).
    """
    album_id = album.get_album_uuid()
    album_name = album.get_album_name()
    user_ids = [user.id for user in users]

    log(
        f"[ALBUM_PERMISSIONS] Adding {len(user_ids)} members to {album_name} "
        f"(access: {access_level})",
        level=LogLevel.PROGRESS,
    )

    # Build AddUsersDto
    album_users_dto = [
        AlbumUserAddDto(
            user_id=UUID(user_id),
            role=access_level,
        )
        for user_id in user_ids
    ]
    add_users_dto = AddUsersDto(album_users=album_users_dto)

    # Call API
    client_wrapper = context.get_client_wrapper()
    client = client_wrapper.get_client()  # AuthenticatedClient
    response = proxy_add_users_to_album(
        album_id=album_id,
        client=client,
        body=add_users_dto,
    )
    if response is not None:
        log_debug(
            f"[ALBUM_PERMISSIONS] Successfully added {len(user_ids)} "
            f"members to {album_name}"
        )
    # else: error handling/logging can be added here
