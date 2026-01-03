
from immich_autotag.logging.utils import setup_logging, log
from immich_autotag.logging.levels import LogLevel
from typeguard import typechecked
from immich_autotag.config.user import FILTER_ASSET_LINKS

@typechecked
def initialize_logging() -> None:
    """
    Inicializa el sistema de logging según si hay filtro de assets o no.
    """
    if FILTER_ASSET_LINKS and len(FILTER_ASSET_LINKS) > 0:
        setup_logging(level=LogLevel.FOCUS)
        log("[LOG] Sistema de logging inicializado: nivel FOCUS (modo filtro)", level=LogLevel.FOCUS)
    else:
        setup_logging(level=LogLevel.PROGRESS)
        log("[LOG] Sistema de logging inicializado: nivel PROGRESS (modo normal)", level=LogLevel.PROGRESS)