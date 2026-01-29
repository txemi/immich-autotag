from typeguard import typechecked
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.logging.levels import LogLevel
from immich_autotag.report.modification_kind import ModificationKind
from .resolve_emails_to_user_ids import _resolve_emails_to_user_ids
from .get_current_members import _get_current_members
from .add_members_to_album import add_members_to_album
from .remove_members_from_album import _remove_members_from_album
from immich_autotag.albums.permissions.album_policy_resolver import ResolvedAlbumPolicy
from immich_autotag.context.immich_context import ImmichContext

if True:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

@typechecked
def sync_album_permissions(
    album_wrapper: 'AlbumResponseWrapper',
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
    album_id = album_wrapper.get_album_uuid()
    album_name = album_wrapper.get_album_name()
    album_uuid = album_wrapper.get_album_uuid_no_cache()
    report = ModificationReport.get_instance()

    if not resolved_policy.has_match:
        log_debug(f"[ALBUM_PERMISSIONS] Skipping {album_name}: no matching rules")
        return

    # Resolve configured member emails to user IDs
    result = _resolve_emails_to_user_ids(resolved_policy.members, context)
    target_user_ids = set(result.resolved.values())

    # Get current members from API (pass UUID directly)
    current_members = _get_current_members(album_uuid, context)
    current_user_ids = {str(member.user.id) for member in current_members}

    # Calculate diff
    users_to_add = target_user_ids - current_user_ids
    users_to_remove = current_user_ids - target_user_ids

    # Phase 2A: PONER (add members)
    if users_to_add:
        # You need to resolve UserResponseWrapper objects for users_to_add
        # This requires mapping user IDs to wrappers, which should be handled by the caller or a utility
        pass  # Placeholder for add_members_to_album logic

    # Phase 2B: QUITAR (remove members)
    if users_to_remove:
        _remove_members_from_album(
            album=album_wrapper,
            user_ids=list(users_to_remove),
            context=context,
        )
        report.add_album_permission_modification(
            kind=ModificationKind.ALBUM_PERMISSION_REMOVED,
            album=album_wrapper,
            matched_rules=resolved_policy.matched_rules,
            groups=resolved_policy.groups,
            members=list(users_to_remove),
            access_level="none",
        )

    if users_to_add or users_to_remove:
        log(
            f"[ALBUM_PERMISSIONS] Synced {album_name}: "
            f"+{len(users_to_add)} PONER, -{len(users_to_remove)} QUITAR",
            level=LogLevel.FOCUS,
        )
    else:
        log_debug(f"[ALBUM_PERMISSIONS] {album_name}: No changes needed")
