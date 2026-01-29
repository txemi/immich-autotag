def setup_profiling_and_memory():
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
