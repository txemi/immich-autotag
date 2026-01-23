import logging

from typeguard import typechecked

from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.manager import ConfigManager
from immich_autotag.logging.levels import LogLevel, LogLevelInfo
from immich_autotag.logging.utils import log, setup_logging


@typechecked
def initialize_logging() -> None:
    """
    Initializes the logging system depending on whether there is an asset filter or not.
    """

    from immich_autotag.config.internal_config import FORCED_LOG_LEVEL

    manager = ConfigManager.get_instance()
    filter_wrapper = FilterConfigWrapper.from_filter_config(manager.config.filters)

    # --- Lógica de forzado de log para desarrollo/CI ---
    if FORCED_LOG_LEVEL is not None:
        # FORCED_LOG_LEVEL ahora es LogLevel (enum), acceder a .value para LogLevelInfo
        forced_info: LogLevelInfo = FORCED_LOG_LEVEL.value
        setup_logging(level=forced_info.level_value)
        log(
            f"[LOG] Logging system initialized: FORCED_LOG_LEVEL={FORCED_LOG_LEVEL.name}",
            level=forced_info.level_value,
        )
    elif filter_wrapper.is_focused():
        setup_logging(level=LogLevel.FOCUS)
        log(
            "[LOG] Logging system initialized: FOCUS level (filter mode)",
            level=LogLevel.FOCUS,
        )
    else:
        setup_logging(level=LogLevel.PROGRESS)
    # Silence HTTP logs from httpx and noisy dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Test logs para cada nivel
    log("[TEST] Log ERROR", level=LogLevel.ERROR)
    log("[TEST] Log IMPORTANT", level=LogLevel.IMPORTANT)
    log("[TEST] Log PROGRESS", level=LogLevel.PROGRESS)
    log("[TEST] Log FOCUS", level=LogLevel.FOCUS)
    log("[TEST] Log DEBUG", level=LogLevel.DEBUG)
    log(
        "[LOG] Logging system initialized: PROGRESS level (forced)",
        level=LogLevel.PROGRESS,
    )
