from __future__ import annotations

from immich_client import Client
from typeguard import typechecked

from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.internal_config import get_immich_base_url
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.load_duplicates_collection import (
    load_duplicates_collection,
)
from immich_autotag.logging.init import initialize_logging
from immich_autotag.permissions import (
    process_album_permissions,
    sync_album_permissions,
)
from immich_autotag.permissions.album_policy_resolver import resolve_album_policy
from immich_autotag.tags.list_tags import list_tags

# --- DUPLICATE STDOUT/STDERR TO LOG FILE (tee4py) ---
from immich_autotag.utils.tee_logging import setup_tee_logging

setup_tee_logging()

# --- Register global exception hook to log time of uncaught exceptions (without changing default behavior) ---
from immich_autotag.utils.exception_hook import setup_exception_hook

setup_exception_hook()


@typechecked
def run_main():
    from immich_autotag.config.manager import ConfigManager
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.utils.user_help import print_welcome_links

    # Get config FIRST, then initialize logging
    manager = ConfigManager.get_instance()
    if not manager or not manager.config or not manager.config.server:
        raise RuntimeError("ConfigManager or server config not initialized")

    # Initialize logging (needs ConfigManager to be ready)
    initialize_logging()

    from immich_autotag.statistics.statistics_manager import StatisticsManager

    StatisticsManager.get_instance().save()  # Force initial statistics file write

    print_welcome_links(manager.config)
    api_key = manager.config.server.api_key
    client = Client(
        base_url=get_immich_base_url(),
        headers={"x-api-key": api_key},
        raise_on_unexpected_status=True,
    )
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

    # --- ALBUM PERMISSIONS: Phase 1 & 2 (BEFORE processing assets)
    # Permissions are fast, assets processing is slow (hours/days)
    process_album_permissions(manager.config, context)
    _sync_all_album_permissions(manager.config, context)

    # Asset filtering logic
    filter_wrapper = FilterConfigWrapper.from_filter_config(manager.config.filters)
    if filter_wrapper.is_focused():
        ruleset = filter_wrapper.get_filter_in_ruleset()
        assets_to_process = ruleset.get_filtered_in_assets_by_uuid(context)

        from immich_autotag.assets.process.process_single_asset import (
            process_single_asset,
        )

        for wrapper in assets_to_process:
            process_single_asset(asset_wrapper=wrapper)
    else:
        # You can change the max_assets value here or pass it as an external argument
        max_assets = None
        process_assets(context, max_assets=max_assets)

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
    print_welcome_links(manager.config)


def _sync_all_album_permissions(user_config, context: ImmichContext) -> None:  # type: ignore
    """
    Phase 2: Synchronize all album permissions.

    Iterates over albums and syncs permissions for those with matching rules.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    if not user_config or not user_config.album_permissions:
        return

    if not user_config.album_permissions.enabled:
        return

    log(
        "[ALBUM_PERMISSIONS] Starting Phase 2 (actual synchronization)...",
        level=LogLevel.FOCUS,
    )

    albums_collection = context.albums_collection
    album_perms_config = user_config.album_permissions

    # Build user groups dictionary for quick lookup
    user_groups_dict = {}
    if album_perms_config.user_groups:
        for group in album_perms_config.user_groups:
            user_groups_dict[group.name] = group

    synced_count = 0
    error_count = 0

    # Process each album
    for album_wrapper in albums_collection.albums:
        album = album_wrapper.album
        try:
            resolved_policy = resolve_album_policy(
                album_name=album.album_name,
                album_id=album.id,
                user_groups=user_groups_dict,
                selection_rules=album_perms_config.selection_rules or [],
            )

            if resolved_policy.has_match:
                sync_album_permissions(
                    album_wrapper=album_wrapper,
                    resolved_policy=resolved_policy,
                    context=context,
                )
                synced_count += 1

        except Exception as e:
            log(
                f"[ALBUM_PERMISSIONS] ERROR processing album {album.album_name}: {e}",
                level=LogLevel.ERROR,
            )
            error_count += 1

    log(
        f"[ALBUM_PERMISSIONS] Phase 2 Summary: {synced_count} synced, {error_count} errors",
        level=LogLevel.FOCUS,
    )
