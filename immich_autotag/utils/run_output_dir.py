import os
from datetime import datetime
from pathlib import Path

from typeguard import typechecked

LOGS_LOCAL_DIR = Path("logs_local")
_RUN_OUTPUT_DIR = None


@typechecked
def find_recent_run_dirs(
    logs_dir: Path, max_age_hours: int = 3, exclude_current: bool = True
) -> list[Path]:
    """
    Devuelve una lista de carpetas de ejecuciones recientes (subdirs con 'PID' en el nombre y fecha válida),
    ordenadas de más reciente a más antigua, filtrando por antigüedad (max_age_hours).
    Si exclude_current es True, excluye la carpeta de la ejecución actual.
    """
    from datetime import datetime, timedelta

    now = datetime.now()
    recent_dirs: list[tuple[datetime, Path]] = []
    current_run_dir = (
        get_run_output_dir(logs_dir).resolve() if exclude_current else None
    )
    for subdir in logs_dir.iterdir():
        if subdir.is_dir() and "PID" in subdir.name:
            try:
                if exclude_current and subdir.resolve() == current_run_dir:
                    continue
            except Exception:
                continue
            try:
                dt_str = subdir.name.split("_PID")[0]
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                if now - dt < timedelta(hours=max_age_hours):
                    recent_dirs.append((dt, subdir))
            except Exception:
                continue
    recent_dirs.sort(reverse=True)
    return [d for _, d in recent_dirs]


@typechecked
def get_run_output_dir(base_dir: Path = LOGS_LOCAL_DIR) -> Path:
    """
    Returns the output directory for the current run. Argument must be a Path.
    """
    global _RUN_OUTPUT_DIR
    if _RUN_OUTPUT_DIR is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        _RUN_OUTPUT_DIR = base_dir / f"{now}_PID{pid}"
        _RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _RUN_OUTPUT_DIR


@typechecked
def get_previous_run_output_dir(base_dir: Path = LOGS_LOCAL_DIR) -> Path | None:
    """
    Searches for the most recent previous execution directory in base_dir (must be Path).
    Returns Path or None if there are no previous executions.
    """
    base = base_dir
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
