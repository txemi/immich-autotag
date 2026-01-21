"""
Log levels for Immich Autotag

Objective: Help developers easily choose an appropriate log level by providing clear, human-friendly names and explanations. Each log level is mapped to a standard logging level or a custom one, and exposes whether it is standard or custom, as well as a description for documentation and dynamic use.
"""

import logging
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class LogLevelInfo:
    level_value: int
    is_custom: bool
    description: str


class LogLevel(Enum):
    ERROR = LogLevelInfo(
        logging.ERROR,
        False,
        "Standard error level. Use for serious problems that need immediate attention.",
    )
    IMPORTANT = LogLevelInfo(
        logging.WARNING,
        False,
        "Standard warning level. Use for important warnings that should not be ignored.",
    )
    WARNING = LogLevelInfo(
        logging.WARNING, False, "Standard warning level. Use for general warnings."
    )
    PROGRESS = LogLevelInfo(
        logging.INFO,
        True,
        "Custom level. Use for progress updates and evolution of long-running processes. These messages should appear in standard application output to inform the user about processing status.",
    )
    INFO = LogLevelInfo(
        logging.INFO,
        False,
        "Standard info level. Use for general informational messages.",
    )
    FOCUS = LogLevelInfo(
        15,
        True,
        "Custom level. Use when the user is focusing on a specific asset and needs detailed information. These messages are hidden in standard mode but shown in focus mode to help with deep debugging or investigation.",
    )
    DEBUG = LogLevelInfo(
        logging.DEBUG,
        False,
        "Standard debug level. Use for low-level debugging information.",
    )

    @property
    def is_custom(self) -> bool:
        return self.value.is_custom

    @property
    def description(self) -> str:
        return self.value.description

    @property
    def level_value(self):
        return self.value.level_value

    def __str__(self):
        return self.name

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
