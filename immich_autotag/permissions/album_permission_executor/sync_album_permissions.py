from dataclasses import dataclass

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
from immich_autotag.users.user_response_wrapper import UserResponseWrapper

from ._resolve_emails_result import EmailMemberResolution

if True:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@dataclass(frozen=True)
class MemberDiff:
    members_to_add: set[UserResponseWrapper]
    members_to_remove: set[UserResponseWrapper]


def _resolve_target_members(
    resolved_policy: ResolvedAlbumPolicy, context: ImmichContext
) -> list[UserResponseWrapper]:
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper

    email_objs = [EmailAddress.from_string(e) for e in resolved_policy.members]
    member_resolution = EmailMemberResolution()
    member_resolution.resolve_emails_to_user_ids(email_objs, context)
    # Only wrap if not already a UserResponseWrapper
    result: list[UserResponseWrapper] = []
    for u in member_resolution.get_resolved_members():
        if isinstance(u, UserResponseWrapper):
            result.append(u)
        else:
            result.append(UserResponseWrapper.from_user(u))
    return result


def _get_current_member_wrappers(
    album_wrapper: "AlbumResponseWrapper",
) -> list[UserResponseWrapper]:
    from immich_autotag.users.user_manager import UserManager

    user_manager = UserManager.get_instance()
    current_members = album_wrapper.get_album_users()
    wrappers: list[UserResponseWrapper] = []
    for album_user in current_members:
        member: UserResponseWrapper | None = user_manager.get_by_uuid(
            album_user.get_uuid()
        )
        if member is None:
            from immich_autotag.logging.utils import log_debug

            log_debug(
                f"[ALBUM_PERMISSIONS] Skipping removal for unresolved album user {album_user.get_uuid()}"
            )
            continue
        wrappers.append(member)
    return wrappers


def _calculate_member_diff(
    target_members: list[UserResponseWrapper],
    current_members: list[UserResponseWrapper],
) -> MemberDiff:
    target_members_set: set[UserResponseWrapper] = set(target_members)
    current_members_set: set[UserResponseWrapper] = set(current_members)
    members_to_add: set[UserResponseWrapper] = target_members_set - current_members_set
    members_to_remove: set[UserResponseWrapper] = (
        current_members_set - target_members_set
    )
    return MemberDiff(
        members_to_add=members_to_add, members_to_remove=members_to_remove
    )


def _apply_member_changes(
    album_wrapper: "AlbumResponseWrapper",
    members_to_add: set[UserResponseWrapper],
    members_to_remove: set[UserResponseWrapper],
    resolved_policy: ResolvedAlbumPolicy,
    context: ImmichContext,
) -> None:
    from immich_autotag.api.logging_proxy.types import AlbumUserRole

    if members_to_add:
        logging_add_members_to_album(
            album=album_wrapper,
            members=list(members_to_add),
            access_level=AlbumUserRole.EDITOR,
            context=context,
            matched_rules=resolved_policy.matched_rules,
            groups=resolved_policy.groups,
        )
    if members_to_remove:
        logging_remove_members_from_album(
            album=album_wrapper,
            members=list(members_to_remove),
            context=context,
            matched_rules=resolved_policy.matched_rules,
            groups=resolved_policy.groups,
        )


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
    album_name: str = album_wrapper.get_album_name()
    if not resolved_policy.has_match:
        log_debug(f"[ALBUM_PERMISSIONS] Skipping {album_name}: no matching rules")
        return
    target_members: list[UserResponseWrapper] = _resolve_target_members(
        resolved_policy, context
    )
    current_member_wrappers: list[UserResponseWrapper] = _get_current_member_wrappers(
        album_wrapper
    )
    # Debug: Ensure all elements are UserResponseWrapper before set operations
    i: int
    x: UserResponseWrapper
    for i, x in enumerate(target_members):
        if not isinstance(x, UserResponseWrapper):
            print(f"[DEBUG] target_members[{i}] is {type(x)}: {x}")
    for i, x in enumerate(current_member_wrappers):
        if not isinstance(x, UserResponseWrapper):
            print(f"[DEBUG] current_member_wrappers[{i}] is {type(x)}: {x}")
    assert all(
        isinstance(x, UserResponseWrapper) for x in target_members
    ), "target_members contains non-UserResponseWrapper"
    assert all(
        isinstance(x, UserResponseWrapper) for x in current_member_wrappers
    ), "current_member_wrappers contains non-UserResponseWrapper"
    member_diff: MemberDiff = _calculate_member_diff(
        target_members, current_member_wrappers
    )
    _apply_member_changes(
        album_wrapper,
        member_diff.members_to_add,
        member_diff.members_to_remove,
        resolved_policy,
        context,
    )
    if member_diff.members_to_add or member_diff.members_to_remove:
        log(
            f"[ALBUM_PERMISSIONS] Synced {album_name}: "
            f"+{len(member_diff.members_to_add)} PONER, -{len(member_diff.members_to_remove)} QUITAR",
            level=LogLevel.FOCUS,
        )
    else:
        log_debug(f"[ALBUM_PERMISSIONS] {album_name}: No changes needed")
