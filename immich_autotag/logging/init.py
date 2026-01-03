from immich_autotag.logging.utils import setup_logging
from immich_autotag.logging.levels import LogLevel
from typeguard import typechecked
from typing import Sequence

@typechecked
def initialize_logging() -> None:
    """
    Inicializa el sistema de logging según si hay filtro de assets o no.
    """
    from immich_autotag.logging.utils import setup_logging
    from immich_autotag.logging.levels import LogLevel

    from immich_autotag.config.user import FILTER_ASSET_LINKS, VERBOSE_LOGGING
    import re

    # Setup logging before any processing
    if FILTER_ASSET_LINKS and len(FILTER_ASSET_LINKS) > 0:
        from immich_autotag.logging.utils import log
        from immich_autotag.logging.levels import LogLevel
        setup_logging(level=LogLevel.FOCUS)
        log("### LOG_DE_PRUEBA_VISIBLE_123456 ###", level=LogLevel.FOCUS)
    else:
        setup_logging(level=LogLevel.PROGRESS)