from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from immich_autotag.albums.permissions.album_policy_resolver import resolve_album_policy
from immich_autotag.config.models import AlbumPermissionsConfig, UserConfig, UserGroup
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.permissions import sync_album_permissions

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


def _report_album_permission_failure(
    album_wrapper: "AlbumResponseWrapper", exc: Exception
) -> None:
    """Log a skipped album's permission failure and record it in the modification report.

    Kept separate from the loop so the caller reads as "try / count / report / continue".
    Anything that goes wrong while *reporting* must not resurrect the exception we just
    swallowed on purpose, hence the inner guard.
    """
    import traceback

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.report.modification_report import ModificationReport

    album_name = album_wrapper.get_album_name()
    tb = traceback.format_exc()
    log(
        f"[ALBUM_PERMISSIONS] SKIPPED '{album_name}' "
        f"({album_wrapper.get_immich_album_url().geturl()}): {exc}\n"
        f"Its sharing is left untouched; the run continues.\nTraceback:\n{tb}",
        level=LogLevel.IMPORTANT,
    )
    try:
        ModificationReport.get_instance().add_modification(
            kind=ModificationKind.ERROR_ALBUM_PERMISSION_SYNC_FAILED,
            album=album_wrapper,
            extra={"error_message": str(exc), "traceback": tb},
        )
    except Exception as report_exc:  # noqa: BLE001 - reporting must never abort the run
        log(
            f"[ALBUM_PERMISSIONS] Could not record the failure of '{album_name}' "
            f"in the report: {report_exc}",
            level=LogLevel.WARNING,
        )


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
            # Fault isolation, and it is the whole point of this try. Permission sync runs
            # BEFORE the asset loop, so an exception here does not cost one album: it kills
            # the run before a single asset is classified, and on the batch branch a failed
            # run also stops the self-chaining -- one bad album buys days of silence.
            # Seen 2026-08-10: Immich answers a duplicate album_user row with a bare 500,
            # which is what a manual share racing the engine looks like from here.
            try:
                sync_album_permissions(
                    album_wrapper=album_wrapper,
                    resolved_policy=resolved_policy,
                    context=context,
                )
            # Broad on purpose: no single album may abort the run.
            except Exception as exc:  # noqa: BLE001
                error_count += 1
                _report_album_permission_failure(album_wrapper, exc)
                continue
            synced_count += 1

    # Not FOCUS: a summary nobody sees is how `error_count` stayed at a hardcoded-looking
    # zero for so long. Errors are announced at a level that survives normal verbosity.
    log(
        f"[ALBUM_PERMISSIONS] Phase 2 Summary: {synced_count} synced, {error_count} errors",
        level=LogLevel.IMPORTANT if error_count else LogLevel.FOCUS,
    )
