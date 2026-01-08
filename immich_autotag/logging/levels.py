from enum import Enum, auto



class LogLevel(Enum):
    ERROR = 40  # Error events that should be logged at a high level
    IMPORTANT = 30  # Important events, warnings, conflicts
    PROGRESS = 20  # General progress, batch info
    FOCUS = 15  # For focus mode: all relevant info for a specific asset (menos prioritario que PROGRESS)
    DEBUG = 10  # Internal details, fine-grained debugging

    def __str__(self):
        return self.name
