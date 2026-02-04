from immich_autotag.logging.levels import LogLevel

from ._internal_types import ErrorHandlingMode

# ==================== API CACHE CONTROL (PER TYPE) ====================
# Control cache usage for each entity type (developer/debug only)
USE_CACHE_ASSETS = True
USE_CACHE_ALBUMS = True
USE_CACHE_ALBUM_PAGES = True
USE_CACHE_USERS = True


# ==================== MULTITHREADING / CONCURRENCY ====================
# Control whether to use ThreadPoolExecutor for asset processing, regardless of MAX_WORKERS value.
# If False, always use direct loop (sequential). If True, use thread pool even for MAX_WORKERS=1.
USE_THREADPOOL = False  # Set to True to force thread pool usage, False for direct loop
# Sequential mode is usually faster for this workload, but you can experiment with USE_THREADPOOL for benchmarking.
MAX_WORKERS = 1  # Set to 1 for sequential processing (recommended for best performance in this environment)

# ==================== DEBUGGING / PROFILING / PERFORMANCE ====================
# Error handling mode (affects debug/trace behavior)
DEFAULT_ERROR_MODE = ErrorHandlingMode.CRAZY_DEBUG
# Enable cProfile CPU profiling regardless of error mode
ENABLE_PROFILING = False  # Set to True to enable cProfile profiling
# Enable tracemalloc memory profiling
ENABLE_MEMORY_PROFILING = False  # Set to False to disable tracemalloc memory profiling

# ==================== MEMORY CONTROL ====================
# Control whether assets are kept in memory (True = keep in memory, False = release after use)
KEEP_ASSETS_IN_MEMORY = False  # Default False; set to True to keep assets in memory

# ==================== ALBUM HANDLING / THRESHOLDS ====================
# Number of errors in the window required to mark an album unavailable
ALBUM_ERROR_THRESHOLD = 3
# Window (seconds) in which errors are counted for the threshold (default: 24 hours)
ALBUM_ERROR_WINDOW_SECONDS = 24 * 3600
# Global threshold: if this many albums are marked unavailable during a run,
# take global action (in DEVELOPMENT this causes fail-fast; in PRODUCTION we log a summary).
GLOBAL_UNAVAILABLE_THRESHOLD = 5
# Enable/disable merging albums with the same name
MERGE_DUPLICATE_ALBUMS_ENABLED = (
    True  # Change to True to enable merging of duplicate albums
)

# ==================== LOGGING CONTROL FOR DEVELOPMENT/CI ====================
# If set to a log level string (e.g., 'DEBUG', 'INFO', 'PROGRESS', 'FOCUS'),
# this will force the global log level for the app, ignoring any other logic.
# If None, normal logic applies.
FORCED_LOG_LEVEL = (
    LogLevel.ASSET_SUMMARY
)  # Change to 'DEBUG' to force massive logging in development/CI

# ==================== ARCHITECTURE IMPORT HOOK CONTROL ====================
# Set to True to enable architecture import hook, False to disable enforcement
ENABLE_ARCHITECTURE_IMPORT_HOOK = True

# ==================== CONVERSIONS AT STARTUP ====================
# Controls whether all conversions are applied to assets at application startup
APPLY_CONVERSIONS_AT_START = False  # Set to False to disable mass processing at startup

# ==================== MAINTENANCE: DELETE CONFLICT TAGS ====================
# If False, disables the maintenance_delete_conflict_tags function (prevents accidental mass deletion)
ENABLE_MAINTENANCE_DELETE_CONFLICT_TAGS = False  # Default: disabled for safety
