from enum import Enum, auto


class ErrorHandlingMode(Enum):
    """
    Internal error handling mode for the application.
    - USER: Continue processing, survive errors, maximize completed work (for end users).
    - DEVELOPMENT: Fail fast, show full traceback and exception (for developers).
    """

    USER = auto()
    DEVELOPMENT = auto()
