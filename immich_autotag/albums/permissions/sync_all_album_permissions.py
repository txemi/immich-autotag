from __future__ import annotations

from typing import Optional

from immich_autotag.albums.permissions.album_policy_resolver import resolve_album_policy
from immich_autotag.config.models import AlbumPermissionsConfig, UserConfig, UserGroup
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.permissions import sync_album_permissions


def sync_all_album_permissions(user_config: Optional[UserConfig], context: ImmichContext) -> None:  # type: ignore
    """
    Phase 2: Synchronize all album permissions.

    Iterates over albums and syncs permissions for those with matching rules.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    if not user_config or not user_config.album_permissions:
        return

    album_perms_config: AlbumPermissionsConfig = user_config.album_permissions  # type: ignore
    if not album_perms_config.enabled:
        return

    log(
        "[ALBUM_PERMISSIONS] Starting Phase 2 (actual synchronization)...",
        level=LogLevel.FOCUS,
    )

    albums_collection = context.get_albums_collection()
    # Build user groups dictionary for quick lookup
    user_groups_dict: dict[str, "UserGroup"] = {}
    user_groups = album_perms_config.user_groups
    if user_groups:
        for group in user_groups:
            user_groups_dict[group.name] = group

    synced_count = 0
    error_count = 0

    # Process each album
    # Use direct attribute access; selection_rules is Optional[List[AlbumSelectionRule]]
    selection_rules = album_perms_config.selection_rules or []
    for album_wrapper in albums_collection.get_albums():
        resolved_policy = resolve_album_policy(
            album=album_wrapper,
            user_groups=user_groups_dict,
            selection_rules=selection_rules or [],
        )

        if resolved_policy.has_match:
            sync_album_permissions(
                album_wrapper=album_wrapper,
                resolved_policy=resolved_policy,
                context=context,
            )
            synced_count += 1

    log(
        f"[ALBUM_PERMISSIONS] Phase 2 Summary: {synced_count} synced, {error_count} errors",
        level=LogLevel.FOCUS,
    )
