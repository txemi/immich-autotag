# internal_config.py
# Centralizes internal variables and global project configuration.

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# These variables are automatically derived and should not be edited by the user.

import attrs
from typeguard import typechecked

from ._internal_types import ErrorHandlingMode


@attrs.define(auto_attribs=True, slots=True, on_setattr=attrs.setters.validate)
class HostPort:
    host: str = attrs.field(validator=attrs.validators.instance_of(str))
    port: int = attrs.field(validator=attrs.validators.instance_of(int))


@typechecked
def _get_host_and_port() -> HostPort:
    # Get host and port from the experimental config singleton
    from immich_autotag.config.manager import (
        ConfigManager,
    )

    manager = ConfigManager.get_instance()
    if not manager or not manager.config or not manager.config.server:
        raise RuntimeError("ConfigManager or server config not initialized")
    return HostPort(host=manager.config.server.host, port=manager.config.server.port)


@typechecked
def get_immich_web_base_url() -> str:
    host_port = _get_host_and_port()
    return f"http://{host_port.host}:{host_port.port}"


def get_immich_base_url():
    # In the future, IMMICH_HOST and IMMICH_PORT will be loaded dynamically from a singleton
    return f"{get_immich_web_base_url()}/api"


IMMICH_PHOTO_PATH_TEMPLATE = "/photos/{id}"

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
