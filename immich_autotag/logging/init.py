import logging

from typeguard import typechecked

from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.manager import ConfigManager
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, setup_logging


@typechecked
def initialize_logging() -> None:
    """
    Initializes the logging system depending on whether there is an asset filter or not.
    """

    manager = ConfigManager.get_instance()
    if manager.config is None:
        raise RuntimeError("ConfigManager.config is not initialized!")
    filter_wrapper = FilterConfigWrapper.from_filter_config(manager.config.filters)
    # Si estamos filtrando miuy pocos assets es psiblemente por diagnostico, subir nivel de log
    if filter_wrapper.is_focused():
        setup_logging(level=LogLevel.FOCUS)
        log(
            "[LOG] Logging system initialized: FOCUS level (filter mode)",
            level=LogLevel.FOCUS,
        )
    else:
        # sino sencillamente reportar progreso
        setup_logging(level=LogLevel.PROGRESS)
        # Silence HTTP logs from httpx and noisy dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Test logs for each level
    log("[TEST] Log ERROR", level=LogLevel.ERROR)
    log("[TEST] Log IMPORTANT", level=LogLevel.IMPORTANT)
    log("[TEST] Log PROGRESS", level=LogLevel.PROGRESS)
    log("[TEST] Log FOCUS", level=LogLevel.FOCUS)
    log("[TEST] Log DEBUG", level=LogLevel.DEBUG)
    log(
        "[LOG] Logging system initialized: PROGRESS level (forced)",
        level=LogLevel.PROGRESS,
    )
