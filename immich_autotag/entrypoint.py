from __future__ import annotations

from immich_client import Client
from typeguard import typechecked

from immich_autotag.albums.album_collection_wrapper import \
    AlbumCollectionWrapper
from immich_autotag.assets.asset_manager import AssetManager
from immich_autotag.assets.process_assets import process_assets
from immich_autotag.config.internal_config import get_immich_base_url
# from immich_autotag.config.user import API_KEY
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.duplicates.duplicate_collection_wrapper import DuplicateCollectionWrapper
from immich_autotag.duplicates.duplicates_loader import DuplicatesLoader
from immich_autotag.duplicates.load_duplicates_collection import load_duplicates_collection
from immich_autotag.logging.init import initialize_logging
from immich_autotag.tags.list_tags import list_tags




@typechecked
def run_main():

    import re

    from immich_autotag.config.user import FILTER_ASSET_LINKS, VERBOSE_LOGGING
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import setup_logging

    # Initialize logging before any processing
    initialize_logging()

    # Get API_KEY from experimental config manager singleton
    from immich_autotag.config.experimental_config.manager import (
        ExperimentalConfigManager, load_experimental_config_at_startup)

    manager = ExperimentalConfigManager.get_instance()
    if not manager or not manager.config or not manager.config.server:
        raise RuntimeError("ExperimentalConfigManager or server config not initialized")
    api_key = manager.config.server.api_key
    client = Client(
        base_url=get_immich_base_url(),
        headers={"x-api-key": api_key},
        raise_on_unexpected_status=True,
    )
    import re

    from immich_autotag.config.user import FILTER_ASSET_LINKS, VERBOSE_LOGGING

    tag_collection = list_tags(client)
    albums_collection = AlbumCollectionWrapper.from_client(client)
    # Load duplicates
    duplicates_collection = load_duplicates_collection(client)
    asset_manager = AssetManager(client=client)
    context = ImmichContext(
        client=client,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
        duplicates_collection=duplicates_collection,
        asset_manager=asset_manager,
    )
    # Asset filtering logic
    if FILTER_ASSET_LINKS and len(FILTER_ASSET_LINKS) > 0:
        # Activate verbose logging
        import immich_autotag.config.user as user_config

        user_config.VERBOSE_LOGGING = True
        asset_ids = []
        # Accept any URL containing a UUID (v4) as asset ID, regardless of path
        uuid_pattern = re.compile(
            r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})"
        )
        for link in FILTER_ASSET_LINKS:
            match = uuid_pattern.search(link)
            if not match:
                raise RuntimeError(
                    f"[ERROR] Could not extract asset ID from link: {link}"
                )
            asset_ids.append(match.group(1))
        # Load only the specified assets
        wrappers = []
        from uuid import UUID

        for asset_id in asset_ids:
            try:
                asset_uuid = UUID(asset_id)
            except Exception:
                raise RuntimeError(
                    f"[ERROR] Invalid asset ID (not a valid UUID): {asset_id}"
                )
            wrapper = asset_manager.get_asset(asset_uuid, context)
            if wrapper is None:
                raise RuntimeError(
                    f"[ERROR] Asset with ID {asset_id} could not be loaded from API."
                )
            wrappers.append(wrapper)
        print(
            f"[INFO] Filtered mode: Only processing {len(wrappers)} asset(s) from FILTER_ASSET_LINKS."
        )
        from threading import Lock

        from immich_autotag.assets.process_single_asset import \
            process_single_asset

        lock = Lock()
        from immich_autotag.report.modification_report import \
            ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        for wrapper in wrappers:
            process_single_asset(
                asset_wrapper=wrapper, tag_mod_report=tag_mod_report, lock=lock
            )
    else:
        # You can change the max_assets value here or pass it as an external argument
        max_assets = None
        process_assets(context, max_assets=max_assets)

    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
