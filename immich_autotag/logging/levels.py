import logging
from enum import Enum


class LogLevel(Enum):
    ERROR = logging.ERROR  # 40
    IMPORTANT = logging.WARNING  # 30
    WARNING = logging.WARNING  # 30
    PROGRESS = logging.INFO  # 20
    FOCUS = 15  # 15 (personalizado)
    DEBUG = logging.DEBUG  # 10

    def __str__(self):
        return self.name
