from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.albums.permissions.sync_all_album_permissions import (
    sync_all_album_permissions,
)
from immich_autotag.utils.typeguard_hook import install_typeguard_import_hook

install_typeguard_import_hook()  # noqa: E402
from immich_autotag.utils.setup_runtime import (  # noqa: E402
    setup_logging_and_exceptions,
)

setup_logging_and_exceptions()  # noqa: E402
if TYPE_CHECKING:
    pass

# Typeguard import hook must be installed before any other imports!


from immich_autotag.albums.albums.album_collection_wrapper import (  # noqa: E402
    AlbumCollectionWrapper,
)
from immich_autotag.assets.asset_manager import AssetManager  # noqa: E402
from immich_autotag.assets.process.process_assets import process_assets  # noqa: E402
from immich_autotag.config.filter_wrapper import FilterConfigWrapper  # noqa: E402
from immich_autotag.config.host_config import get_immich_base_url  # noqa: E402
from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_context import ImmichContext  # noqa: E402
from immich_autotag.duplicates.load_duplicates_collection import (  # noqa: E402
    load_duplicates_collection,
)
from immich_autotag.logging.init import initialize_logging  # noqa: E402
from immich_autotag.permissions import (  # noqa: E402
    process_album_permissions,
)
from immich_autotag.tags.list_tags import list_tags  # noqa: E402
from immich_autotag.types import ImmichClient  # noqa: E402


def _run_main_inner() -> None:
    manager = _init_config_and_logging()
    client, client_wrapper = _init_client(manager)
    _maintenance_cleanup_labels(client)
    tag_collection, albums_collection, context = _init_collections_and_context(
        client, client_wrapper
    )
    _force_full_album_loading(albums_collection)
    _process_permissions(manager, context)
    _process_assets_or_filtered(manager, context)
    _finalize(manager, client)



from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper


def _init_config_and_logging() -> ConfigManager:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.user_help import print_welcome_links

    manager = ConfigManager.get_instance()
    log("Initializing ConfigManager...", level=LogLevel.INFO)
    if manager.config is None:
        log(
            "FATAL: ConfigManager.config is None after initialization. This suggests the config file failed to load properly. Check ~/.config/immich_autotag/config.py or config.yaml",
            level=LogLevel.ERROR,
        )
        raise RuntimeError("ConfigManager.config is None after initialization")
    log("ConfigManager initialized successfully", level=LogLevel.INFO)
    initialize_logging()
    from immich_autotag.statistics.statistics_manager import StatisticsManager

    StatisticsManager.get_instance().save()
    print_welcome_links(manager.config)
    return manager




def _init_client(manager: ConfigManager) -> tuple[ImmichClient, ImmichClientWrapper]:
    api_key = manager.config.server.api_key
    client = ImmichClient(
        base_url=get_immich_base_url(),
        token=api_key,
        prefix="",
        auth_header_name="x-api-key",
        raise_on_unexpected_status=True,
    )
    from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

    client_wrapper = ImmichClientWrapper.create_default_instance(client)
    return client, client_wrapper


def _maintenance_cleanup_labels(client: ImmichClient) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper

    deleted_count = TagCollectionWrapper.maintenance_delete_conflict_tags(client)
    if deleted_count > 0:
        log(
            f"[CLEANUP] Deleted {deleted_count} duplicate/conflict autotag labels.",
            level=LogLevel.INFO,
        )


def _init_collections_and_context(
    client: ImmichClient, client_wrapper: ImmichClientWrapper
) -> tuple[list, AlbumCollectionWrapper, ImmichContext]:
    tag_collection = list_tags(client)
    albums_collection = AlbumCollectionWrapper.from_client()
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
    return tag_collection, albums_collection, context


def _force_full_album_loading(albums_collection: AlbumCollectionWrapper) -> None:
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

    albums_collection.ensure_all_full(perf_phase_tracker=perf_phase_tracker)


def _process_permissions(manager: ConfigManager, context: ImmichContext) -> None:
    process_album_permissions(manager.config, context)
    sync_all_album_permissions(manager.config, context)


def _process_assets_or_filtered(manager: ConfigManager, context: ImmichContext) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

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
        import time

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


def _finalize(manager: ConfigManager, client: ImmichClient) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper

    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
    from immich_autotag.utils.user_help import print_welcome_links

    print_welcome_links(manager.config)
    deleted_count = TagCollectionWrapper.maintenance_delete_conflict_tags(client)
    if deleted_count > 0:
        log(
            f"[CLEANUP] Deleted {deleted_count} duplicate/conflict autotag labels.",
            level=LogLevel.INFO,
        )


def run_main():
    """
    Wrapper that runs _run_main_inner, and if error mode is CRAZY_DEBUG, activates cProfile and saves the result in profile_debug.stats.
    """
    from immich_autotag.config.internal_config import (
        ENABLE_MEMORY_PROFILING,
        ENABLE_PROFILING,
    )

    if ENABLE_MEMORY_PROFILING:
        from immich_autotag.utils.perf.memory_profiler import setup_tracemalloc_snapshot

        setup_tracemalloc_snapshot()
    if ENABLE_PROFILING:
        from immich_autotag.utils.perf.cprofile_profiler import setup_cprofile_profiler

        setup_cprofile_profiler()
    _run_main_inner()
