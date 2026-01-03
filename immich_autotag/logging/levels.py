from enum import Enum, auto


class LogLevel(Enum):
    FOCUS = 15  # For focus mode: all relevant info for a specific asset (menos prioritario que PROGRESS)
    IMPORTANT = 30  # Important events, warnings, conflicts
    PROGRESS = 20  # General progress, batch info
    DEBUG = 10  # Internal details, fine-grained debugging

    def __str__(self):
        return self.name
