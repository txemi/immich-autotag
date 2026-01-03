
import logging
from .levels import LogLevel
from typeguard import typechecked
from typing import Any

# Map our custom levels to logging module levels
LOGLEVEL_TO_LOGGING = {
    LogLevel.FOCUS: 15,      # Menor que INFO (20)
    LogLevel.IMPORTANT: logging.WARNING,
    LogLevel.PROGRESS: logging.INFO,
    LogLevel.DEBUG: logging.DEBUG,
}

# Register custom level for FOCUS if not already present
if not hasattr(logging, 'FOCUS'):
    logging.addLevelName(15, 'FOCUS')

@typechecked
def log(msg: str, level: LogLevel = LogLevel.PROGRESS) -> None:
    lvl = LOGLEVEL_TO_LOGGING.get(level, logging.INFO)
    # Only emit FOCUS logs if the current logging level is set to FOCUS (15)
    current_level = logging.getLogger().getEffectiveLevel()
    if level == LogLevel.FOCUS and current_level > lvl:
        return  # Suppress FOCUS logs in PROGRESS or higher modes
    logging.log(lvl, msg)

@typechecked
def setup_logging(level: LogLevel = LogLevel.PROGRESS) -> None:
    logging.basicConfig(
        format='[%(levelname)s] %(message)s',
        level=LOGLEVEL_TO_LOGGING.get(level, logging.INFO)
    )
