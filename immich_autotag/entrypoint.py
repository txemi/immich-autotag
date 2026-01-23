from __future__ import annotations

from typeguard import typechecked

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.albums.permissions.album_policy_resolver import resolve_album_policy
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.host_config import get_immich_base_url
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.load_duplicates_collection import (
    load_duplicates_collection,
)
from immich_autotag.logging.init import initialize_logging
from immich_autotag.permissions import (
    process_album_permissions,
    sync_album_permissions,
)
from immich_autotag.tags.list_tags import list_tags
from immich_autotag.types import ImmichClient

# --- DUPLICATE STDOUT/STDERR TO LOG FILE (tee4py) ---
from immich_autotag.utils.tee_logging import setup_tee_logging

setup_tee_logging()

# --- Register global exception hook to log time of uncaught exceptions (without changing default behavior) ---
from immich_autotag.utils.exception_hook import setup_exception_hook

setup_exception_hook()


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
        resolved_policy = resolve_album_policy(
            album_name=album_wrapper.get_album_name(),
            album_id=album_wrapper.get_album_id(),
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

    log(
        f"[ALBUM_PERMISSIONS] Phase 2 Summary: {synced_count} synced, {error_count} errors",
        level=LogLevel.FOCUS,
    )


@typechecked
def run_main():

    from immich_autotag.config.manager import ConfigManager
    from immich_autotag.logging.levels import LogLevel

    # Get config FIRST (constructor initializes it)
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.user_help import print_welcome_links

    log("Initializing ConfigManager...", level=LogLevel.INFO)
    manager = ConfigManager.get_instance()

    # Verify config is actually loaded before doing anything else
    if manager.config is None:
        log(
            "FATAL: ConfigManager.config is None after initialization. This suggests the config file failed to load properly. Check ~/.config/immich_autotag/config.py or config.yaml",
            level=LogLevel.ERROR,
        )
        raise RuntimeError("ConfigManager.config is None after initialization")

    log("ConfigManager initialized successfully", level=LogLevel.INFO)

    # Now initialize logging (needs ConfigManager.config to be ready)
    initialize_logging()

    from immich_autotag.statistics.statistics_manager import StatisticsManager

    StatisticsManager.get_instance().save()  # Force initial statistics file write

    print_welcome_links(manager.config)
    api_key = manager.config.server.api_key
    client = ImmichClient(
        base_url=get_immich_base_url(),
        token=api_key,
        prefix="",  # Immich uses x-api-key, not Bearer token
        auth_header_name="x-api-key",
        raise_on_unexpected_status=True,
    )
    # Initialize the context ONLY with the client (others as None or empty)
    context = ImmichContext.create_instance(
        client=client,
        albums_collection=None,
        tag_collection=None,
        duplicates_collection=None,
        asset_manager=None,
    )
    # Now, create the dependent objects
    tag_collection = list_tags(client)

    # Initialize the singleton and load albums from API
    albums_collection = AlbumCollectionWrapper.from_client(client)
    # --- LOG LAZY LOAD DE ÁLBUMES ---
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

    perf_phase_tracker.mark("lazy", "start")
    albums_collection.log_lazy_load_timing()
    perf_phase_tracker.mark("lazy", "end")
    duplicates_collection = load_duplicates_collection(client)
    asset_manager = AssetManager(client=client)
    # Assign the objects to the context
    context.albums_collection = albums_collection
    context.tag_collection = tag_collection
    context.duplicates_collection = duplicates_collection
    context.asset_manager = asset_manager

    # --- FORCE FULL LOADING OF ALL ALBUMS BEFORE ASSET ITERATION ---
    import time

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    perf_phase_tracker.mark("full", "start")
    log(
        "[PROGRESS] [ALBUM-FULL-LOAD] Inicio carga full de álbumes",
        level=LogLevel.PROGRESS,
    )
    t0 = time.time()
    albums_collection._ensure_all_albums_full()
    t1 = time.time()
    log(
        f"[PROGRESS] [ALBUM-FULL-LOAD] Fin carga full de álbumes. Elapsed: {t1-t0:.2f} seconds.",
        level=LogLevel.PROGRESS,
    )
    perf_phase_tracker.mark("full", "end")

    # --- ALBUM PERMISSIONS: Phase 1 & 2 (BEFORE processing assets)
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
        perf_phase_tracker.mark("assets", "start")
        log(
            "[PROGRESS] [ASSET-PROCESS] Inicio procesado de activos",
            level=LogLevel.PROGRESS,
        )
        t0 = time.time()
        process_assets(context)
        t1 = time.time()
        log(
            f"[PROGRESS] [ASSET-PROCESS] Fin procesado de activos. Elapsed: {t1-t0:.2f} seconds.",
            level=LogLevel.PROGRESS,
        )
        perf_phase_tracker.mark("assets", "end")

    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
    print_welcome_links(manager.config)
