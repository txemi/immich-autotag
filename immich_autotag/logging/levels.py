
"""
Log levels for Immich Autotag

Objective: Help developers easily choose an appropriate log level by providing clear, human-friendly names and explanations. Each log level is mapped to a standard logging level or a custom one, and exposes whether it is standard or custom, as well as a description for documentation and dynamic use.
"""

import logging
from enum import Enum

class LogLevel(Enum):
    ERROR = (logging.ERROR, False, "Standard error level. Use for serious problems that need immediate attention.")
    IMPORTANT = (logging.WARNING, False, "Standard warning level. Use for important warnings that should not be ignored.")
    WARNING = (logging.WARNING, False, "Standard warning level. Use for general warnings.")
    PROGRESS = (logging.INFO, True, "Custom level. Use for progress updates and evolution of long-running processes. These messages should appear in standard application output to inform the user about processing status.")
    INFO = (logging.INFO, False, "Standard info level. Use for general informational messages.")
    FOCUS = (15, True, "Custom level. Use when the user is focusing on a specific asset and needs detailed information. These messages are hidden in standard mode but shown in focus mode to help with deep debugging or investigation.")
    DEBUG = (logging.DEBUG, False, "Standard debug level. Use for low-level debugging information.")

    def __init__(self, level_value, is_custom, description):
        self._level_value = level_value
        self._is_custom = is_custom
        self._description = description

    @property
    def is_custom(self) -> bool:
        """Return True if this is a custom (non-standard) log level."""
        return self._is_custom

    @property
    def description(self) -> str:
        """Return a human-friendly description of the log level."""
        return self._description

    @property
    def value(self):
        return self._level_value

    def __str__(self):
        return self.name
