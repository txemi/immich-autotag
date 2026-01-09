import logging
from typing import Any

from typeguard import typechecked

from .levels import LogLevel

## No longer necessary to map LOGLEVEL_TO_LOGGING, we use LogLevel.value directly


# Register the FOCUS level ALWAYS before any setup_logging
def register_focus_level():
    if not hasattr(logging, "FOCUS"):
        logging.addLevelName(15, "FOCUS")


register_focus_level()


@typechecked
def log(msg: str, level: LogLevel = LogLevel.PROGRESS) -> None:
    logging.log(level.value, msg)


@typechecked
def setup_logging(level: LogLevel = LogLevel.PROGRESS) -> None:
    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=level.value,
        force=True,
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
    return logging.getLogger().isEnabledFor(level.value)
