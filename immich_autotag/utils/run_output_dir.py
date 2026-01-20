import os
from datetime import datetime
from pathlib import Path

from typeguard import typechecked

LOGS_LOCAL_DIR = Path("logs_local")
_RUN_OUTPUT_DIR = None

# --- Internal constants for execution folders ---
_RUN_DIR_PID_MARK = "PID"
_RUN_DIR_PID_SEP = "_PID"
_RUN_DIR_DATE_FORMAT = "%Y%m%d_%H%M%S"


# --- Reusable private functions for execution folders ---
@typechecked
def _is_run_dir(subdir: Path) -> bool:
    """Returns True if the subfolder is an execution folder (contains _RUN_DIR_PID_MARK in the name)."""
    return subdir.is_dir() and _RUN_DIR_PID_MARK in subdir.name


@typechecked
def _extract_datetime_from_run_dir(subdir: Path) -> datetime | None:
    """Extracts the date from the execution folder (YYYYMMDD_HHMMSS before _RUN_DIR_PID_SEP)."""
    try:
        dt_str = subdir.name.split(_RUN_DIR_PID_SEP)[0]
        return datetime.strptime(dt_str, _RUN_DIR_DATE_FORMAT)
    except Exception:
        return None


@typechecked
def _list_run_dirs(base_dir: Path) -> list[Path]:
    """Returns all valid execution subfolders in base_dir."""
    return [d for d in base_dir.iterdir() if _is_run_dir(d)]


@typechecked
def find_recent_run_dirs(
    logs_dir: Path, max_age_hours: int = 3, exclude_current: bool = True
) -> list[Path]:
    """
    Returns a list of recent execution folders (subdirs with 'PID' in the name and a valid date),
    sorted from most recent to oldest, filtered by age (max_age_hours).
    If exclude_current is True, excludes the current execution folder.
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    current_run_dir = (
        get_run_output_dir(logs_dir).resolve() if exclude_current else None
    )
    recent_dirs: list[tuple[datetime, Path]] = []
    for subdir in _list_run_dirs(logs_dir):
        try:
            if exclude_current and subdir.resolve() == current_run_dir:
                continue
        except Exception:
            continue
        dt = _extract_datetime_from_run_dir(subdir)
        if dt is not None and now - dt < timedelta(hours=max_age_hours):
            recent_dirs.append((dt, subdir))
    recent_dirs.sort(reverse=True)
    return [d for _, d in recent_dirs]


@typechecked
def get_run_output_dir(base_dir: Path = LOGS_LOCAL_DIR) -> Path:
    """
    Returns the output directory for the current run. Argument must be a Path.
    """
    global _RUN_OUTPUT_DIR
    if _RUN_OUTPUT_DIR is None:
        now = datetime.now().strftime(_RUN_DIR_DATE_FORMAT)
        pid = os.getpid()
        _RUN_OUTPUT_DIR = base_dir / f"{now}{_RUN_DIR_PID_SEP}{pid}"
        _RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _RUN_OUTPUT_DIR


@typechecked
def get_previous_run_output_dir(base_dir: Path = LOGS_LOCAL_DIR) -> Path | None:
    """
    Searches for the most recent previous execution folder in base_dir.
    Returns Path or None if there are no previous executions.
    """
    base = base_dir
    if not base.exists() or not base.is_dir():
        return None
    dirs = _list_run_dirs(base)
    if not dirs:
        return None
    current = get_run_output_dir(base_dir)
    # Sort by descending date using the private function
    dirs.sort(
        key=lambda d: _extract_datetime_from_run_dir(d) or datetime.min,
        reverse=True,
    )
    for d in dirs:
        if d != current:
            return d
    return None
