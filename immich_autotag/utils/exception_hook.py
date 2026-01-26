"""
exception_hook.py

Utility to log the exact time when the process ends due to an uncaught exception,
without changing Python's default behavior.
"""

import sys
from datetime import datetime


def setup_exception_hook():
    """
    Installs a sys.excepthook that calls the original and then prints the exception
    time.
    """
    _original_excepthook = sys.excepthook

    def custom_excepthook(exc_type, exc_value, exc_traceback):
        _original_excepthook(exc_type, exc_value, exc_traceback)
        print(
            f"[ERROR] Process terminated by uncaught exception at "
            f"{datetime.now().isoformat()}"
        )
        try:
            from immich_autotag.statistics.statistics_manager import StatisticsManager
            from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker

            StatisticsManager.get_instance().abrupt_exit()
            perf_phase_tracker.log_summary()
        except Exception as e:
            print(f"[ERROR] Could not save abrupt exit time or log perf summary: {e}")

    sys.excepthook = custom_excepthook
