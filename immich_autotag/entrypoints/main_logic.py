from __future__ import annotations


def run_main_inner_logic():
    from immich_autotag.entrypoint.assets import process_assets_or_filtered
    from immich_autotag.entrypoint.collections import (
        force_full_album_loading,
        init_collections_and_context,
    )
    from immich_autotag.entrypoint.finalize import finalize
    from immich_autotag.entrypoint.init import init_client, init_config_and_logging
    from immich_autotag.entrypoint.maintenance import maintenance_cleanup_labels
    from immich_autotag.entrypoint.permissions import process_permissions

    manager = init_config_and_logging()
    client_wrapper = init_client(manager)
    client = client_wrapper.get_client()
    # Initialize context early so it's available for maintenance operations
    context = init_collections_and_context(client_wrapper)
    # Maintenance: delete unhealthy temporary albums
    from immich_autotag.albums.maintenance_tasks.delete_unhealthy_temp_albums import delete_unhealthy_temp_albums
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
