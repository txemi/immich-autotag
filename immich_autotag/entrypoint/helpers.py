from __future__ import annotations
from typing import TYPE_CHECKING

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.host_config import get_immich_base_url
from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.load_duplicates_collection import load_duplicates_collection
from immich_autotag.logging.init import initialize_logging
from immich_autotag.permissions import process_album_permissions
from immich_autotag.tags.list_tags import list_tags
from immich_autotag.types import ImmichClient
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.albums.permissions.sync_all_album_permissions import sync_all_album_permissions


def init_config_and_logging() -> ConfigManager:
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

... (remaining code omitted for brevity) ...

from __future__ import annotations
from typing import TYPE_CHECKING

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.host_config import get_immich_base_url
from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.load_duplicates_collection import load_duplicates_collection
from immich_autotag.logging.init import initialize_logging
from immich_autotag.permissions import process_album_permissions
from immich_autotag.tags.list_tags import list_tags
from immich_autotag.types import ImmichClient
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.albums.permissions.sync_all_album_permissions import sync_all_album_permissions


def init_config_and_logging() -> ConfigManager:
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


def init_client(manager: ConfigManager) -> tuple[ImmichClient, ImmichClientWrapper]:
    api_key = manager.config.server.api_key
    client = ImmichClient(
        base_url=get_immich_base_url(),
        token=api_key,
        prefix="",
        auth_header_name="x-api-key",
        raise_on_unexpected_status=True,
    )
    client_wrapper = ImmichClientWrapper.create_default_instance(client)
    return client, client_wrapper


def maintenance_cleanup_labels(client: ImmichClient) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper
    deleted_count = TagCollectionWrapper.maintenance_delete_conflict_tags(client)
    if deleted_count > 0:
        log(
            f"[CLEANUP] Deleted {deleted_count} duplicate/conflict autotag labels.",
            level=LogLevel.INFO,
        )


def init_collections_and_context(
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


def force_full_album_loading(albums_collection: AlbumCollectionWrapper) -> None:
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker
    albums_collection.ensure_all_full(perf_phase_tracker=perf_phase_tracker)


def process_permissions(manager: ConfigManager, context: ImmichContext) -> None:
    process_album_permissions(manager.config, context)
    sync_all_album_permissions(manager.config, context)


def process_assets_or_filtered(manager: ConfigManager, context: ImmichContext) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker
    filter_wrapper = FilterConfigWrapper.from_filter_config(manager.config.filters)
    if filter_wrapper.is_focused():
        ruleset = filter_wrapper.get_filter_in_ruleset()
        assets_to_process = ruleset.get_filtered_in_assets_by_uuid(context)

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


def finalize(manager: ConfigManager, client: ImmichClient) -> None:
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
