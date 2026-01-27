from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.entrypoint.assets import process_assets_or_filtered
from immich_autotag.entrypoint.collections import (
    force_full_album_loading,
    init_collections_and_context,
)
from immich_autotag.entrypoint.finalize import finalize
from immich_autotag.entrypoint.init import init_client, init_config_and_logging
from immich_autotag.entrypoint.maintenance import maintenance_cleanup_labels
from immich_autotag.entrypoint.permissions import process_permissions
from immich_autotag.utils.typeguard_hook import install_typeguard_import_hook

install_typeguard_import_hook()  # noqa: E402
from immich_autotag.utils.setup_runtime import (  # noqa: E402
    setup_logging_and_exceptions,
)

setup_logging_and_exceptions()  # noqa: E402
if TYPE_CHECKING:
    pass

# Typeguard import hook must be installed before any other imports!


def run_main_inner() -> None:
    manager = init_config_and_logging()
    client_wrapper = init_client(manager)
    client = client_wrapper.get_client()
    maintenance_cleanup_labels(client)
    context = init_collections_and_context(client_wrapper)
    albums_collection = context.get_albums_collection()
    force_full_album_loading(albums_collection)
    process_permissions(manager, context)
    process_assets_or_filtered(manager, context)
    finalize(manager, client)


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
    run_main_inner()
