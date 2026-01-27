from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.entrypoint.assets import _process_assets_or_filtered
from immich_autotag.entrypoint.collections import _init_collections_and_context, _force_full_album_loading
from immich_autotag.entrypoint.finalize import _finalize
from immich_autotag.entrypoint.init import _init_config_and_logging, _init_client
from immich_autotag.entrypoint.maintenance import _maintenance_cleanup_labels
from immich_autotag.entrypoint.permissions import _process_permissions
from immich_autotag.utils.typeguard_hook import install_typeguard_import_hook

install_typeguard_import_hook()  # noqa: E402
from immich_autotag.utils.setup_runtime import (  # noqa: E402
    setup_logging_and_exceptions,
)

setup_logging_and_exceptions()  # noqa: E402
if TYPE_CHECKING:
    pass

# Typeguard import hook must be installed before any other imports!


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
