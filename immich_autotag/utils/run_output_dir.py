import os
from datetime import datetime
from pathlib import Path

from typeguard import typechecked

LOGS_LOCAL_DIR = Path("logs_local")
_RUN_OUTPUT_DIR = None


# --- Funciones privadas reutilizables para carpetas de ejecuciones ---
@typechecked
def _is_run_dir(subdir: Path) -> bool:
    """Devuelve True si la subcarpeta es de ejecución (contiene 'PID' en el nombre)."""
    return subdir.is_dir() and "PID" in subdir.name


@typechecked
def _extract_datetime_from_run_dir(subdir: Path) -> datetime | None:
    """Extrae la fecha de la carpeta de ejecución (YYYYMMDD_HHMMSS antes de _PID)."""
    try:
        dt_str = subdir.name.split("_PID")[0]
        return datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
    except Exception:
        return None


@typechecked
def _list_run_dirs(base_dir: Path) -> list[Path]:
    """Devuelve todas las subcarpetas válidas de ejecución en base_dir."""
    return [d for d in base_dir.iterdir() if _is_run_dir(d)]


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
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        _RUN_OUTPUT_DIR = base_dir / f"{now}_PID{pid}"
        _RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _RUN_OUTPUT_DIR


@typechecked
def get_previous_run_output_dir(base_dir: Path = LOGS_LOCAL_DIR) -> Path | None:
    """
    Busca la carpeta de la ejecución anterior más reciente en base_dir.
    Devuelve Path o None si no hay ejecuciones previas.
    """
    base = base_dir
    if not base.exists() or not base.is_dir():
        return None
    dirs = _list_run_dirs(base)
    if not dirs:
        return None
    current = get_run_output_dir(base_dir)
    # Ordenar por fecha descendente usando la función privada
    dirs.sort(
        key=lambda d: _extract_datetime_from_run_dir(d) or datetime.min, reverse=True
    )
    for d in dirs:
        if d != current:
            return d
    return None
