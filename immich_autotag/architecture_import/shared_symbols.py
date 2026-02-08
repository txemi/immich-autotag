from pathlib import Path

import immich_autotag.api
from immich_autotag.api import immich_proxy, logging_proxy

# Root directory of the Immich-autotag project
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
IMMICH_PROXY_MODULE_NAME = immich_proxy.__name__
LOGGING_PROXY_MODULE_NAME = logging_proxy.__name__
IMMICH_CLIENT_PREFIX = "immich_client"
IMMICH_PROXY_PREFIX = immich_proxy.__name__
IMMICH_API_MODULE = immich_autotag.api.__name__
