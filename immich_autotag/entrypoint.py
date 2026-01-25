from __future__ import annotations

import atexit
import os
from typing import TYPE_CHECKING, Optional

from typeguard import typechecked

from immich_autotag.config.models import UserConfig
from immich_autotag.utils.typeguard_hook import install_typeguard_import_hook

install_typeguard_import_hook()  # noqa: E402
from immich_autotag.utils.setup_runtime import (  # noqa: E402
    setup_logging_and_exceptions,
)

setup_logging_and_exceptions()  # noqa: E402
if TYPE_CHECKING:
    from immich_autotag.config.models import AlbumPermissionsConfig, UserGroup

# Typeguard import hook must be installed before any other imports!


from immich_autotag.albums.albums.album_collection_wrapper import (  # noqa: E402
    AlbumCollectionWrapper,
)
from immich_autotag.albums.permissions.album_policy_resolver import (  # noqa: E402
    resolve_album_policy,
)
from immich_autotag.assets.asset_manager import AssetManager  # noqa: E402
from immich_autotag.assets.process.process_assets import process_assets  # noqa: E402
from immich_autotag.config.filter_wrapper import FilterConfigWrapper  # noqa: E402
from immich_autotag.config.host_config import get_immich_base_url  # noqa: E402
from immich_autotag.context.immich_context import ImmichContext  # noqa: E402
from immich_autotag.duplicates.load_duplicates_collection import (  # noqa: E402
    load_duplicates_collection,
)
from immich_autotag.logging.init import initialize_logging  # noqa: E402
from immich_autotag.permissions import (  # noqa: E402
    process_album_permissions,
    sync_album_permissions,
)
from immich_autotag.tags.list_tags import list_tags  # noqa: E402
from immich_autotag.types import ImmichClient  # noqa: E402


def _sync_all_album_permissions(user_config: Optional[UserConfig], context: ImmichContext) -> None:  # type: ignore
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

    albums_collection = context.albums_collection
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
            album_name=album_wrapper.get_album_name(),
            album_id=album_wrapper.get_album_id(),
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


@typechecked
def _run_main_inner():

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
    from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

    client_wrapper = ImmichClientWrapper.create_default_instance(client)
    # Pasa la clase wrapper, no el cliente crudo, al contexto
    tag_collection = list_tags(client)
    albums_collection = AlbumCollectionWrapper.from_client(client)
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

    perf_phase_tracker.mark(phase="lazy", event="start")
    albums_collection.log_lazy_load_timing()
    perf_phase_tracker.mark(phase="lazy", event="end")
    duplicates_collection = load_duplicates_collection(client)
    asset_manager = AssetManager(client=client)  # type: ignore
    context = ImmichContext.create_default_instance(
        client=client_wrapper,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
        duplicates_collection=duplicates_collection,
        asset_manager=asset_manager,
    )

    # --- FORCE FULL LOADING OF ALL ALBUMS BEFORE ASSET ITERATION ---
    import time

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    albums_collection.ensure_all_full(perf_phase_tracker=perf_phase_tracker)

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
        perf_phase_tracker.mark(phase="assets", event="start")
        log(
            "[PROGRESS] [ASSET-PROCESS] Starting asset processing",
            level=LogLevel.PROGRESS,
        )
        t0 = time.time()
        process_assets(context)
        t1 = time.time()
        log(
            f"[PROGRESS] [ASSET-PROCESS] Finished asset processing. Elapsed: {t1-t0:.2f} seconds.",
            level=LogLevel.PROGRESS,
        )
        perf_phase_tracker.mark(phase="assets", event="end")

    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
    print_welcome_links(manager.config)


def run_main():
    """
    Wrapper que ejecuta _run_main_inner, y si el modo de error es CRAZY_DEBUG, activa cProfile y guarda el resultado en profile_debug.stats.
    """
    import cProfile

    from immich_autotag.config._internal_types import ErrorHandlingMode
    from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE

    if DEFAULT_ERROR_MODE == ErrorHandlingMode.CRAZY_DEBUG:
        import datetime

        from immich_autotag.utils.run_output_dir import get_run_output_dir

        profiler = cProfile.Profile()
        profiler.enable()

        def _save_profile():
            profiler.disable()
            run_dir = get_run_output_dir()
            ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            pid = os.getpid()
            profile_path = run_dir / f"profile_{ts}_PID{pid}.stats"
            profiler.dump_stats(str(profile_path))
            print(f"[PROFILE] cProfile stats saved to {profile_path}")

        atexit.register(_save_profile)
        _run_main_inner()
    else:
        _run_main_inner()
