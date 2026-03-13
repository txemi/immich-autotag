def setup_profiling_and_memory():
    from immich_autotag.config.internal_config import (
        ENABLE_DEADLOCK_STALL_WATCHDOG,
        ENABLE_MEMORY_PROFILING,
        ENABLE_PROFILING,
        STALL_WATCHDOG_CHECK_INTERVAL_SECONDS,
        STALL_WATCHDOG_DUMP_COOLDOWN_SECONDS,
        STALL_WATCHDOG_THRESHOLD_SECONDS,
    )

    if ENABLE_MEMORY_PROFILING:
        from immich_autotag.utils.perf.memory_profiler import setup_tracemalloc_snapshot

        setup_tracemalloc_snapshot()
    if ENABLE_PROFILING:
        from immich_autotag.utils.perf.cprofile_profiler import setup_cprofile_profiler

        setup_cprofile_profiler()
    if ENABLE_DEADLOCK_STALL_WATCHDOG:
        from immich_autotag.utils.perf.stall_watchdog import setup_stall_watchdog

        setup_stall_watchdog(
            enabled=True,
            check_interval_seconds=STALL_WATCHDOG_CHECK_INTERVAL_SECONDS,
            stall_threshold_seconds=STALL_WATCHDOG_THRESHOLD_SECONDS,
            dump_cooldown_seconds=STALL_WATCHDOG_DUMP_COOLDOWN_SECONDS,
        )
