from enum import Enum, auto


import logging

class LogLevel(Enum):
    ERROR = logging.ERROR
    IMPORTANT = logging.WARNING
    PROGRESS = logging.INFO
    FOCUS = 15  # Personalizado, menor que INFO
    DEBUG = logging.DEBUG

    def __str__(self):
        return self.name
