"""
Process Album Permissions

Phase 1: Detection & logging (dry-run)
Phase 2: (Placeholder for future synchronization)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.albums.permissions.album_policy_resolver import resolve_album_policy
from immich_autotag.context.immich_context import ImmichContext

if TYPE_CHECKING:
    from immich_autotag.config.models import UserConfig


@typechecked
def process_album_permissions(
    user_config: "UserConfig", context: ImmichContext
) -> None:
    """
    Phase 1: Process album permissions (dry-run detection and logging).

    This function resolves album policies based on configured selection rules and logs
    which albums would be shared with which groups. No API calls are made in Phase 1.
    """
    from immich_autotag.config.models import UserConfig
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.tags.modification_kind import ModificationKind

    if not user_config or not isinstance(user_config, UserConfig):
        return

    album_perms_config = user_config.album_permissions
    if not album_perms_config or not album_perms_config.enabled:
        return

    log(
        "[ALBUM_PERMISSIONS] Starting Phase 1 (dry-run detection)...",
        level=LogLevel.FOCUS,
    )

    report = ModificationReport.get_instance()
    albums_collection = context.albums_collection

    # Build user groups dictionary for quick lookup
    user_groups_dict = {}
    if album_perms_config.user_groups:
        for group in album_perms_config.user_groups:
            user_groups_dict[group.name] = group

    # Process each album
    matched_count = 0
    unmatched_count = 0
    for album_wrapper in albums_collection.albums:
        resolved_policy = resolve_album_policy(
            album_name=album_wrapper.get_album_name(),
            album_id=album_wrapper.get_album_id(),
            user_groups=user_groups_dict,
            selection_rules=album_perms_config.selection_rules or [],
        )

        if resolved_policy.has_match:
            matched_count += 1
            log(
                f"[ALBUM_PERMISSIONS] Album '{album_wrapper.get_album_name()}' → "
                f"Groups: {resolved_policy.groups}, "
                f"Members: {len(resolved_policy.members)}, "
                f"Access: {resolved_policy.access_level}",
                level=LogLevel.DEBUG,
            )
            # Record in modification report
            report.add_album_permission_modification(
                kind=ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
                album=album_wrapper,
                matched_rules=resolved_policy.matched_rules,
                groups=resolved_policy.groups,
                members=resolved_policy.members,
                access_level=resolved_policy.access_level,
            )
        else:
            unmatched_count += 1
            if album_perms_config.log_unmatched:
                log(
                    f"[ALBUM_PERMISSIONS] Album '{album_wrapper.get_album_name()}' → No matching rules",
                    level=LogLevel.DEBUG,
                )
                report.add_album_permission_modification(
                    kind=ModificationKind.ALBUM_PERMISSION_NO_MATCH,
                    album=album_wrapper,
                    matched_rules=[],
                    groups=[],
                    members=[],
                    access_level="none",
                )

    log(
        f"[ALBUM_PERMISSIONS] Summary: {matched_count} matched, {unmatched_count} unmatched",
        level=LogLevel.FOCUS,
    )
