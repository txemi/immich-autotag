

import logging
from typing import Any

from typeguard import typechecked

from .levels import LogLevel



# Map our custom levels to logging module levels
LOGLEVEL_TO_LOGGING = {
    LogLevel.IMPORTANT: logging.WARNING,
    LogLevel.PROGRESS: logging.INFO,
    LogLevel.FOCUS: 15,  # Menor que INFO (20)
    LogLevel.DEBUG: logging.DEBUG,
}

# Register custom level for FOCUS if not already present
if not hasattr(logging, "FOCUS"):
    logging.addLevelName(15, "FOCUS")


@typechecked
def log(msg: str, level: LogLevel = LogLevel.PROGRESS) -> None:
    # Si FORCE_LOG_LEVEL está definido, forzamos ese nivel
    # El nivel de log es el que se pasa en la llamada
    logging.log(LOGLEVEL_TO_LOGGING[level], msg)


@typechecked
def setup_logging(level: LogLevel = LogLevel.PROGRESS) -> None:
    # Si FORCE_LOG_LEVEL está definido, usarlo como nivel global
    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=LOGLEVEL_TO_LOGGING.get(level, logging.INFO),
    )
@typechecked
def log_debug(msg: str) -> None:
    """
    Log a debug message with [BUG] tag, always at DEBUG level.
    """
    logging.log(logging.DEBUG, msg)


@typechecked
def is_log_level_enabled(level: LogLevel) -> bool:
    """
    Returns True if the given log level is enabled for the root logger.
    Usage: if is_log_level_enabled(LogLevel.DEBUG): ...
    """
    import logging
    py_level = LOGLEVEL_TO_LOGGING.get(level, logging.INFO)
    return logging.getLogger().isEnabledFor(py_level)    