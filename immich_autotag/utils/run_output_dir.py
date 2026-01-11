import os
from datetime import datetime
from pathlib import Path

from typeguard import typechecked

_RUN_OUTPUT_DIR = None


@typechecked
def get_run_output_dir(base_dir="logs_local") -> Path:
    global _RUN_OUTPUT_DIR
    if _RUN_OUTPUT_DIR is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        _RUN_OUTPUT_DIR = Path(base_dir) / f"{now}_PID{pid}"
        _RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _RUN_OUTPUT_DIR


@typechecked
def get_previous_run_output_dir(base_dir="logs_local") -> Path | None:
    """
    Searches for the most recent previous execution directory in base_dir.
    Returns Path or None if there are no previous executions.
    """
    base = Path(base_dir)
    if not base.exists() or not base.is_dir():
        return None
    # Filter only folders with expected format
    dirs = [d for d in base.iterdir() if d.is_dir() and "PID" in d.name]
    if not dirs:
        return None

    # Sort by date in the name (YYYYMMDD_HHMMSS)
    def extract_datetime(d):
        try:
            dt_str = d.name.split("_PID")[0]
            return datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
        except Exception:
            return datetime.min

    dirs.sort(key=extract_datetime, reverse=True)
    # Return the most recent (that is not the current one)
    current = get_run_output_dir(base_dir)
    for d in dirs:
        if d != current:
            return d
    return None
