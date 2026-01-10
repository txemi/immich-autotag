
"""
exception_hook.py

Utility to log the exact time when the process ends due to an uncaught exception, without changing Python's default behavior.
"""

import sys
from datetime import datetime

def setup_exception_hook():
    """
    Installs a sys.excepthook that calls the original and then prints the exception time.
    """
    _original_excepthook = sys.excepthook
    def custom_excepthook(exc_type, exc_value, exc_traceback):
        _original_excepthook(exc_type, exc_value, exc_traceback)
        print(f"[ERROR] Process terminated by uncaught exception at {datetime.now().isoformat()}")
    sys.excepthook = custom_excepthook
