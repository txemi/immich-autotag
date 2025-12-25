# internal_config.py
# Centralizes internal variables and global project configuration.

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# These variables are automatically derived and should not be edited by the user.
from immich_autotag.config.user import IMMICH_HOST, IMMICH_PORT
IMMICH_WEB_BASE_URL = f"http://{IMMICH_HOST}:{IMMICH_PORT}"
IMMICH_BASE_URL = f"{IMMICH_WEB_BASE_URL}/api"
IMMICH_PHOTO_PATH_TEMPLATE = "/photos/{id}"
# ==================== LOG CONFIGURATION ====================
PRINT_ASSET_DETAILS = False  # Set to True to enable detailed per-asset logging
# Control whether to use ThreadPoolExecutor for asset processing, regardless of MAX_WORKERS value.
# If False, always use direct loop (sequential). If True, use thread pool even for MAX_WORKERS=1.
USE_THREADPOOL = False  # Set to True to force thread pool usage, False for direct loop
# Sequential mode is usually faster for this workload, but you can experiment with USE_THREADPOOL for benchmarking.
MAX_WORKERS = 1  # Set to 1 for sequential processing (recommended for best performance in this environment)
