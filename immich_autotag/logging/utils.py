import logging

from typeguard import typechecked

from .levels import LogLevel

# No longer necessary to map LOGLEVEL_TO_LOGGING, we use LogLevel.value directly


# Register the FOCUS level ALWAYS before any setup_logging


def register_custom_log_levels():
    """
    Register all custom (non-standard) log levels defined in LogLevel.
    This avoids hardcoding which levels are custom; instead, each LogLevel knows if it is custom.
    addLevelName() is idempotent, so it's safe to call multiple times.
    """
    existing_levels = logging.getLevelNamesMapping()
    for level in LogLevel:
        if level.is_custom() and level.name not in existing_levels:
            logging.addLevelName(level.level_value(), level.name)


register_custom_log_levels()


@typechecked
def log(msg: str, level: LogLevel = LogLevel.PROGRESS) -> None:
    logging.log(level.level_value(), msg)


@typechecked
def setup_logging(level: LogLevel = LogLevel.PROGRESS) -> None:
    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=level.level_value(),
        force=True,
    )


@typechecked
def log_debug(msg: str) -> None:
    """
    Log a debug message with [BUG] tag, always at DEBUG level.
    """
    logging.log(logging.DEBUG, msg)


@typechecked
def log_trace(msg: str) -> None:
    """
    Log a trace message at TRACE level (ultra-verbose, diagnostic-only).
    """
    from .levels import LogLevel

    logging.log(LogLevel.TRACE.level_value(), msg)


@typechecked
def is_log_level_enabled(level: LogLevel) -> bool:
    """
    Returns True if the given log level is enabled for the root logger.
    Usage: if is_log_level_enabled(LogLevel.DEBUG): ...
    """
    return logging.getLogger().isEnabledFor(level.level_value())
