import os
from datetime import datetime
from pathlib import Path

from typeguard import typechecked

_RUN_OUTPUT_DIR = None


@typechecked
def get_run_output_dir(base_dir="logs") -> Path:
    global _RUN_OUTPUT_DIR
    if _RUN_OUTPUT_DIR is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        _RUN_OUTPUT_DIR = Path(base_dir) / f"{now}_PID{pid}"
        _RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _RUN_OUTPUT_DIR


@typechecked
def get_previous_run_output_dir(base_dir="logs") -> Path | None:
    """
    Busca el directorio de ejecución previa más reciente en base_dir.
    Retorna Path o None si no hay ejecuciones previas.
    """
    base = Path(base_dir)
    if not base.exists() or not base.is_dir():
        return None
    # Filtrar solo carpetas con formato esperado
    dirs = [d for d in base.iterdir() if d.is_dir() and "PID" in d.name]
    if not dirs:
        return None

    # Ordenar por fecha en el nombre (YYYYMMDD_HHMMSS)
    def extract_datetime(d):
        try:
            dt_str = d.name.split("_PID")[0]
            return datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
        except Exception:
            return datetime.min

    dirs.sort(key=extract_datetime, reverse=True)
    # Retornar la más reciente (que no sea la actual)
    current = get_run_output_dir(base_dir)
    for d in dirs:
        if d != current:
            return d
    return None
