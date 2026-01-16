from __future__ import annotations

from immich_client import Client
from typeguard import typechecked

from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.albums.album_policy_resolver import resolve_album_policy
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.internal_config import get_immich_base_url
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.load_duplicates_collection import (
    load_duplicates_collection,
)
from immich_autotag.logging.init import initialize_logging
from immich_autotag.tags.list_tags import list_tags

# --- DUPLICATE STDOUT/STDERR TO LOG FILE (tee4py) ---
from immich_autotag.utils.tee_logging import setup_tee_logging

setup_tee_logging()

# --- Register global exception hook to log time of uncaught exceptions (without changing default behavior) ---
from immich_autotag.utils.exception_hook import setup_exception_hook

setup_exception_hook()


@typechecked
def _process_album_permissions(user_config, context: ImmichContext) -> None:
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
    for album in albums_collection.values():
        resolved_policy = resolve_album_policy(
            album_name=album.album_name,
            album_id=album.id,
            user_groups=user_groups_dict,
            selection_rules=album_perms_config.selection_rules or [],
        )

        if resolved_policy.has_match:
            matched_count += 1
            log(
                f"[ALBUM_PERMISSIONS] Album '{album.album_name}' → "
                f"Groups: {resolved_policy.groups}, "
                f"Members: {len(resolved_policy.members)}, "
                f"Access: {resolved_policy.access_level}",
                level=LogLevel.DEBUG,
            )
            # Record in modification report
            report.add_album_permission_modification(
                kind=ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
                album=album,
                matched_rules=resolved_policy.matched_rules,
                groups=resolved_policy.groups,
                members=resolved_policy.members,
                access_level=resolved_policy.access_level,
            )
        else:
            unmatched_count += 1
            if album_perms_config.log_unmatched:
                log(
                    f"[ALBUM_PERMISSIONS] Album '{album.album_name}' → No matching rules",
                    level=LogLevel.DEBUG,
                )
                report.add_album_permission_modification(
                    kind=ModificationKind.ALBUM_PERMISSION_NO_MATCH,
                    album=album,
                    matched_rules=[],
                    groups=[],
                    members=[],
                    access_level="none",
                )

    log(
        f"[ALBUM_PERMISSIONS] Summary: {matched_count} matched, {unmatched_count} unmatched",
        level=LogLevel.FOCUS,
    )


@typechecked
def run_main():
    import re

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.utils.user_help import print_welcome_links

    # Initialize logging before any processing
    initialize_logging()

    from immich_autotag.statistics.statistics_manager import StatisticsManager

    StatisticsManager.get_instance().save()  # Force initial statistics file write

    # Get API_KEY from experimental config manager singleton
    from immich_autotag.config.manager import (
        ConfigManager,
    )

    manager = ConfigManager.get_instance()
    if not manager or not manager.config or not manager.config.server:
        raise RuntimeError("ConfigManager or server config not initialized")
    print_welcome_links(manager.config)
    api_key = manager.config.server.api_key
    client = Client(
        base_url=get_immich_base_url(),
        headers={"x-api-key": api_key},
        raise_on_unexpected_status=True,
    )
    import re

    tag_collection = list_tags(client)
    albums_collection = AlbumCollectionWrapper.from_client(client)
    # Load duplicates
    duplicates_collection = load_duplicates_collection(client)
    asset_manager = AssetManager(client=client)
    context = ImmichContext.create_instance(
        client=client,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
        duplicates_collection=duplicates_collection,
        asset_manager=asset_manager,
    )
    # Asset filtering logic
    filter_wrapper = FilterConfigWrapper.from_filter_config(manager.config.filters)
    if filter_wrapper.is_focused():
        ruleset = filter_wrapper.get_filter_in_ruleset()
        assets_to_process = ruleset.get_filtered_in_assets_by_uuid(context)

        from threading import Lock

        from immich_autotag.assets.process.process_single_asset import (
            process_single_asset,
        )
        from immich_autotag.report.modification_report import ModificationReport

        lock = Lock()
        tag_mod_report = ModificationReport.get_instance()
        for wrapper in assets_to_process:
            process_single_asset(
                asset_wrapper=wrapper, tag_mod_report=tag_mod_report, lock=lock
            )
    else:
        # You can change the max_assets value here or pass it as an external argument
        max_assets = None
        process_assets(context, max_assets=max_assets)

    # --- ALBUM PERMISSIONS: Phase 1 (Dry-run detection and logging)
    _process_album_permissions(manager.config, context)

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
    print_welcome_links(manager.config)
