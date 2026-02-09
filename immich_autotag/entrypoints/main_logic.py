from __future__ import annotations


def run_main_inner_logic():
    from immich_autotag.entrypoint.assets import process_assets_or_filtered
    from immich_autotag.entrypoint.collections import (
        force_full_album_loading,
        init_collections_and_context,
    )
    from immich_autotag.entrypoint.finalize import finalize
    from immich_autotag.entrypoint.init import init_config_and_logging
    from immich_autotag.entrypoint.maintenance import maintenance_cleanup_labels
    from immich_autotag.entrypoint.permissions import process_permissions

    manager = init_config_and_logging()
    from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

    client_wrapper = ImmichClientWrapper.get_default_instance()
    client = client_wrapper.get_client()
    # Initialize context early so it's available for maintenance operations
    context = init_collections_and_context(client_wrapper)
    # Maintenance: delete unhealthy temporary albums
    from immich_autotag.albums.maintenance_tasks.delete_unhealthy_temp_albums import (
        delete_unhealthy_temp_albums,
    )
    from immich_autotag.config.internal_config import ENABLE_ALBUM_CLEANUP_RESCUE

    if ENABLE_ALBUM_CLEANUP_RESCUE:
        from immich_autotag.albums.albums.duplicates_manager.rename_strategy.cleanup_rescue import (
            run_album_cleanup_rescue,
        )

        print(
            "[MAINTENANCE] Album cleanup rescue mode enabled. Running rescue operation..."
        )
        run_album_cleanup_rescue()
        print(
            "[MAINTENANCE] Rescue operation completed. Checking for duplicate album names..."
        )
        return
    # Check for duplicate album names after rescue
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )
    from immich_autotag.albums.albums.duplicates_manager.rename_strategy.find_duplicate_names import (
        find_duplicate_album_names,
    )

    collection = AlbumCollectionWrapper.get_instance()
    duplicates = find_duplicate_album_names(collection)
    if duplicates:
        raise RuntimeError(
            f"Duplicate album names still exist after rescue: {duplicates}"
        )
    print("[MAINTENANCE] No duplicate album names found. Asset processing is skipped.")

    delete_unhealthy_temp_albums(context)
    # TODO: Maintenance cleanup disabled during stability testing - causes performance issues
    maintenance_cleanup_labels(client)

    # Apply conversions to all assets before loading tags
    from immich_autotag.config.internal_config import APPLY_CONVERSIONS_AT_START
    from immich_autotag.entrypoint.collections import (
        apply_conversions_to_all_assets_early,
    )

    if APPLY_CONVERSIONS_AT_START:
        apply_conversions_to_all_assets_early(context)
    albums_collection = context.get_albums_collection()


    force_full_album_loading(albums_collection)

    process_permissions(manager, context)
    process_assets_or_filtered(manager, context)
    finalize(manager, client)
