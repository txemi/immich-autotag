from typeguard import typechecked

from immich_autotag.albums.permissions.album_policy_resolver import ResolvedAlbumPolicy
from immich_autotag.api.logging_proxy.albums.album_permissions import (
    logging_add_members_to_album,
    logging_remove_members_from_album,
)
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.types.email_address import EmailAddress

from ._resolve_emails_result import EmailMemberResolution

if True:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@typechecked
def sync_album_permissions(
    album_wrapper: "AlbumResponseWrapper",
    resolved_policy: ResolvedAlbumPolicy,
    context: ImmichContext,
) -> None:
    """
    Phase 2: Synchronize album permissions with configured rules.
    Complete sync strategy: config is source of truth.
    - PONER (add): Members in config but not in album
    - QUITAR (remove): Members in album but not in config
    Args:
        album_wrapper: Album wrapper with album data
        resolved_policy: Resolved policy with target members (emails)
        context: ImmichContext with API client
    """
    # album_id = album_wrapper.get_album_uuid()  # removed unused variable
    album_name = album_wrapper.get_album_name()

    if not resolved_policy.has_match:
        log_debug(f"[ALBUM_PERMISSIONS] Skipping {album_name}: no matching rules")
        return

    # Resolve configured member emails to user objects
    email_objs = [EmailAddress.from_string(e) for e in resolved_policy.members]
    member_resolution = EmailMemberResolution()
    member_resolution.resolve_emails_to_user_ids(email_objs, context)

    # Get current members from API
    current_members = album_wrapper.get_album_users()

    from immich_autotag.users.user_manager import UserManager

    user_manager = UserManager.get_instance()

    current_member_wrappers: list[UserResponseWrapper] = []
    for album_user in current_members:
        member: UserResponseWrapper | None = user_manager.get_by_uuid(album_user.get_uuid())
        if member is None:
            log_debug(
                "[ALBUM_PERMISSIONS] Skipping removal for unresolved album user "
                f"{album_user.get_uuid()}"
            )
            continue
        current_member_wrappers.append(member)

    # Build sets for comparison: target members vs current members
    # Wrap UserResponseDto in UserResponseWrapper for hashability
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper
    target_members: list[UserResponseWrapper] = [UserResponseWrapper.from_user(u) for u in member_resolution.get_resolved_members()]
    target_members_set: set[UserResponseWrapper] = set(target_members)
    current_members_set: set[UserResponseWrapper] = set(current_member_wrappers)

    # Calculate diff
    members_to_add: set[UserResponseWrapper] = target_members_set - current_members_set
    members_to_remove: set[UserResponseWrapper] = current_members_set - target_members_set

    # Phase 2A: PONER (add members)
    if members_to_add:
        from immich_autotag.api.logging_proxy.types import AlbumUserRole

        logging_add_members_to_album(
            album=album_wrapper,
            members=list(members_to_add),
            access_level=AlbumUserRole.EDITOR,
            context=context,
            matched_rules=resolved_policy.matched_rules,
            groups=resolved_policy.groups,
        )

    # Phase 2B: QUITAR (remove members)
    if members_to_remove:
        logging_remove_members_from_album(
            album=album_wrapper,
            members=list(members_to_remove),
            context=context,
            matched_rules=resolved_policy.matched_rules,
            groups=resolved_policy.groups,
        )

    if members_to_add or members_to_remove:
        log(
            f"[ALBUM_PERMISSIONS] Synced {album_name}: "
            f"+{len(members_to_add)} PONER, -{len(members_to_remove)} QUITAR",
            level=LogLevel.FOCUS,
        )
    else:
        log_debug(f"[ALBUM_PERMISSIONS] {album_name}: No changes needed")
