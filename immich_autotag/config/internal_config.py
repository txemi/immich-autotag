# internal_config.py
# Centralizes internal variables and global project configuration.

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# These variables are automatically derived and should not be edited by the user.

import attrs
from typeguard import typechecked

from ._internal_types import ErrorHandlingMode


# Control whether to use ThreadPoolExecutor for asset processing, regardless of MAX_WORKERS value.
# If False, always use direct loop (sequential). If True, use thread pool even for MAX_WORKERS=1.
USE_THREADPOOL = False  # Set to True to force thread pool usage, False for direct loop
# Sequential mode is usually faster for this workload, but you can experiment with USE_THREADPOOL for benchmarking.
MAX_WORKERS = 1  # Set to 1 for sequential processing (recommended for best performance in this environment)

# Internal usage example:
DEFAULT_ERROR_MODE = ErrorHandlingMode.DEVELOPMENT

# Album error handling thresholds (tunable)
# Number of errors in the window required to mark an album unavailable
ALBUM_ERROR_THRESHOLD = 3
# Window (seconds) in which errors are counted for the threshold (default: 24 hours)
ALBUM_ERROR_WINDOW_SECONDS = 24 * 3600
# Global threshold: if this many albums are marked unavailable during a run,
# take global action (in DEVELOPMENT this causes fail-fast; in PRODUCTION we
# log a summary). Default is an absolute count.
GLOBAL_UNAVAILABLE_THRESHOLD = 5


# Flag to enable/disable the functionality of merging albums with the same name
MERGE_DUPLICATE_ALBUMS_ENABLED = (
    True  # Change to True to enable merging of duplicate albums
)
