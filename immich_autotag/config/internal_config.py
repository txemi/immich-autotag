# internal_config.py
# Centralizes internal variables and global project configuration.

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# These variables are automatically derived and should not be edited by the user.

from typeguard import typechecked


@typechecked
def _get_host_and_port() -> tuple[str, int]:
    # Get host and port from the experimental config singleton
    from immich_autotag.config.manager import (
        ConfigManager,
    )

    manager = ConfigManager.get_instance()
    if not manager or not manager.config or not manager.config.server:
        raise RuntimeError("ConfigManager or server config not initialized")
    return manager.config.server.host, manager.config.server.port


@typechecked
def get_immich_web_base_url() -> str:
    host, port = _get_host_and_port()
    return f"http://{host}:{port}"


def get_immich_base_url():
    # In the future, IMMICH_HOST and IMMICH_PORT will be loaded dynamically from a singleton
    return f"{get_immich_web_base_url()}/api"


IMMICH_PHOTO_PATH_TEMPLATE = "/photos/{id}"
# ==================== LOG CONFIGURATION ====================
PRINT_ASSET_DETAILS = False  # Set to True to enable detailed per-asset logging
# Control whether to use ThreadPoolExecutor for asset processing, regardless of MAX_WORKERS value.
# If False, always use direct loop (sequential). If True, use thread pool even for MAX_WORKERS=1.
USE_THREADPOOL = False  # Set to True to force thread pool usage, False for direct loop
# Sequential mode is usually faster for this workload, but you can experiment with USE_THREADPOOL for benchmarking.
MAX_WORKERS = 1  # Set to 1 for sequential processing (recommended for best performance in this environment)
