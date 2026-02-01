"""
Log levels for Immich Autotag

Objective: Help developers easily choose an appropriate log level by providing clear, human-friendly names and explanations. Each log level is mapped to a standard logging level or a custom one, and exposes whether it is standard or custom, as well as a description for documentation and dynamic use.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from typing_extensions import final


@final
@dataclass(frozen=True)
class LogLevelInfo:
    """Immutable metadata for log levels. Cannot be subclassed, modified, or extended with new attributes."""

    __slots__ = ()
    level_value: int
    is_custom: bool
    description: str


class LogLevel(Enum):
    """
    Custom log levels for Immich Autotag.

    Verbosity order (intention):
        ERROR > WARNING = IMPORTANT? > PROGRESS = INFO? > ASSET_SUMMARY > FOCUS > DEBUG > TRACE

    Intention: Make it easy for developers to choose log levels that match the purpose and context of their messages.
    - Use PROGRESS for progress updates (e.g., percent complete, phase changes) that should be visible to users monitoring long-running processes.
    - Use ASSET_SUMMARY for brief, per-asset status messages during large batch operations. Shows a concise result for each asset (e.g., processed, skipped, error), but avoids the full verbosity of FOCUS. Ideal for monitoring batch progress with enough detail to spot issues, without overwhelming output.
    - Use FOCUS for detailed information about a specific asset or entity, especially when debugging or investigating a single item. FOCUS is more verbose than INFO but less than DEBUG, and is ideal for targeted runs.
    - Use INFO for general, high-level informational messages about the application's state or actions.
    - Use DEBUG for very verbose, low-level details, typically when you want to see everything for deep troubleshooting. DEBUG may produce a lot of output and is not recommended for normal runs.
    - Use WARNING, IMPORTANT, and ERROR for issues, warnings, and errors as in standard logging.

    This class provides clear, human-friendly names and explanations, and exposes the numeric value for each level in its description.
    """

    ERROR = LogLevelInfo(
        logging.ERROR,
        False,
        "Standard error level (numeric: 40). Use for serious problems that need immediate attention.",
    )
    IMPORTANT = LogLevelInfo(
        logging.WARNING,
        False,
        "Standard warning level (numeric: 30). Use for important warnings that should not be ignored.",
    )
    WARNING = LogLevelInfo(
        logging.WARNING,
        False,
        "Standard warning level (numeric: 30). Use for general warnings.",
    )
    PROGRESS = LogLevelInfo(
        logging.INFO,
        True,
        "Custom level (numeric: 20). Use for progress updates (e.g., percent complete, phase changes) in long-running processes. Intended for user-facing progress feedback.",
    )
    INFO = LogLevelInfo(
        logging.INFO,
        False,
        "Standard info level (numeric: 20). Use for general, high-level informational messages about the application's state or actions.",
    )
    ASSET_SUMMARY = LogLevelInfo(
        17,
        True,
        "Custom level (numeric: 17). Use for brief, per-asset status messages during large batch operations. Shows a concise result for each asset (e.g., processed, skipped, error), but avoids the full verbosity of FOCUS. Ideal for monitoring batch progress with enough detail to spot issues, without overwhelming output.",
    )
    FOCUS = LogLevelInfo(
        15,
        True,
        "Custom level (numeric: 15). Use for detailed information about a specific asset or entity, especially when debugging or investigating a single item. More verbose than INFO, less than DEBUG. Ideal for targeted runs and focused analysis.",
    )

    DEBUG = LogLevelInfo(
        logging.DEBUG,
        False,
        "Standard debug level (numeric: 10). Use for very verbose, low-level details. Typically used when you want to see everything for deep troubleshooting. Not recommended for normal runs. Use TRACE for output that es even more excessive or redundant than DEBUG.",
    )
    TRACE = LogLevelInfo(
        5,
        True,
        "Custom level (numeric: 5). Use for ultra-verbose, excessive, or diagnostic-only output that is not useful even for most debugging sessions. Only enable when you need to trace every detail for deep diagnostics or performance tuning.",
    )

    def is_custom(self) -> bool:
        """Returns True if this is a custom (non-standard) log level."""
        return self.value.is_custom

    def description(self) -> str:
        """Returns the human-friendly description of this log level."""
        return self.value.description

    def level_value(self) -> int:
        """Returns the numeric value of this log level."""
        return self.value.level_value

    def __str__(self):
        return self.name
