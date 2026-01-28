
# Nueva importación: RunExecution está en execution.py
from .execution import RunExecution
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class RunOutputManager:
    # --- Class constants and variables for execution management ---
    LOGS_LOCAL_DIR = Path("logs_local")
    _RUN_DIR_PID_MARK = "PID"
    _RUN_DIR_PID_SEP = "_PID"
    _RUN_DIR_DATE_FORMAT = "%Y%m%d_%H%M%S"
    _RUN_OUTPUT_DIR: Optional[Path] = None

    @staticmethod
    def _is_run_dir(subdir: Path) -> bool:
        """
        Returns True if the subfolder is an execution folder (contains _RUN_DIR_PID_MARK in the name).
        """
        return subdir.is_dir() and RunOutputManager._RUN_DIR_PID_MARK in subdir.name

    @staticmethod
    def _extract_datetime_from_run_dir(subdir: Path) -> Optional[datetime]:
        """
        Extracts the date from the execution folder (YYYYMMDD_HHMMSS before _RUN_DIR_PID_SEP).
        """
        try:
            dt_str = subdir.name.split(RunOutputManager._RUN_DIR_PID_SEP)[0]
            return datetime.strptime(dt_str, RunOutputManager._RUN_DIR_DATE_FORMAT)
        except Exception:
            return None

    @staticmethod
    def _list_run_dirs(base_dir: Path) -> list[Path]:
        """Returns all valid execution subfolders in base_dir."""
        return [d for d in base_dir.iterdir() if RunOutputManager._is_run_dir(d)]

    @classmethod
    def get_run_output_dir(cls, base_dir: Path | None = None) -> RunExecution:
        """
        Returns a RunExecution object for the current run. Argument must be a Path.
        """
        if cls._RUN_OUTPUT_DIR is None:
            if base_dir is None:
                base_dir = cls.LOGS_LOCAL_DIR
            now = datetime.now().strftime(cls._RUN_DIR_DATE_FORMAT)
            pid = os.getpid()
            cls._RUN_OUTPUT_DIR = Path(base_dir) / f"{now}{cls._RUN_DIR_PID_SEP}{pid}"
            cls._RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return RunExecution(cls._RUN_OUTPUT_DIR)

    @classmethod
    def find_recent_run_dirs(
        cls, *, logs_dir: Optional[Path] = None, max_age_hours: int = 3, exclude_current: bool = True
    ) -> list['RunExecution']:
        """
        Devuelve una lista de objetos RunExecution para las ejecuciones recientes (subcarpetas con 'PID' en el nombre y fecha válida),
        ordenadas de más reciente a más antigua, filtradas por edad (max_age_hours).
        Si exclude_current es True, excluye la carpeta de la ejecución actual.
        """
        if logs_dir is None:
            logs_dir = cls.LOGS_LOCAL_DIR
        now = datetime.now()
        current_run = cls.get_run_output_dir(logs_dir) if exclude_current else None
        current_run_dir = current_run.path if current_run else None
        recent_dirs: list[tuple[datetime, Path]] = []
        for subdir in cls._list_run_dirs(logs_dir):
            try:
                if exclude_current and subdir.resolve() == current_run_dir:
                    continue
            except Exception:
                continue
            dt = cls._extract_datetime_from_run_dir(subdir)
            if dt is not None and now - dt < timedelta(hours=max_age_hours):
                recent_dirs.append((dt, subdir))
        recent_dirs.sort(reverse=True)
        return [RunExecution(d) for _, d in recent_dirs]

    @classmethod
    def get_previous_run_output_dir(cls, base_dir: Optional[Path] = None) -> Optional[RunExecution]:
        """
        Searches for the most recent previous execution folder in base_dir.
        Returns Path or None if there are no previous executions.
        """
        if base_dir is None:
            base = cls.LOGS_LOCAL_DIR
        else:
            base = Path(base_dir)
        if not base.exists() or not base.is_dir():
            return None
        dirs = cls._list_run_dirs(base)
        if not dirs:
            return None
        current = cls.get_run_output_dir(base)
        dirs.sort(
            key=lambda d: cls._extract_datetime_from_run_dir(d) or datetime.min,
            reverse=True,
        )
        for d in dirs:
            if d != current.path:
                return RunExecution(d)
        return None

    """
    RunOutputManager centralizes and abstracts the management of output paths and persistence (logs, statistics, caches, reports, etc.)
    for a specific system execution.

    ---
    PURPOSE AND MOTIVATION:
    ----------------------
    In complex systems, multiple subsystems need to save or read data related to the current (or previous) execution:
    logs, statistics, caches, reports, performance profiles, etc. If each subsystem manages paths and folders on its own,
    traceability is lost, evolution becomes harder, and post-mortem analysis and cleanup are more difficult.

    This object solves that problem by centralizing path and persistence logic:
    - Each subsystem asks this object where to save or find its data.
    - The folder and naming structure is unified and can evolve centrally.
    - It can be instantiated for previous runs to coherently find historical data.

    OBJECTIVES:
    ----------
    - Avoid duplication and dispersion of path and persistence logic.
    - Improve traceability and cleanup of each run's outputs.
    - Make it easy to evolve the output structure without breaking subsystems.
    - Enable simple post-mortem analysis and debugging of previous runs.

    TYPICAL USAGE:
    --------------
    - For the current run: `manager = RunOutputManager()`
    - For a previous run: `manager = RunOutputManager(run_dir=Path(...))`
    - To save a log: `manager.get_log_path("my_log")`
    - To save statistics: `manager.get_stats_path("stats")`
    - To create/use a cache: `manager.get_cache_dir("my_cache")`
    - For arbitrary paths: `manager.get_custom_path("subdir", "file.txt")`

    ---
    If you need to save or find any data related to a run, always use this object.
    """
    _current_instance = None

    def __init__(self, run_dir: Optional[Path] = None, base_dir: Optional[Path] = None):
        if run_dir is not None:
            self.run_dir = Path(run_dir).resolve()
        else:
            if base_dir is None:
                base_dir = Path(__file__).resolve().parent.parent / "logs_local"
            base_dir = Path(base_dir).resolve()
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            pid = os.getpid()
            self.run_dir = base_dir / f"{now}_PID{pid}"
            self.run_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def current(cls, base_dir: Optional[Path] = None):
        """
        Returns the singleton instance associated with the current execution.
        If it does not exist, it creates it.
        """
        if cls._current_instance is None:
            cls._current_instance = cls(base_dir=base_dir)
        return cls._current_instance

    def get_log_path(self, name: str) -> Path:
        """Returns the path for a specific log of this run."""
        return self.run_dir / f"{name}.log"

    def get_stats_path(self, name: str) -> Path:
        """Returns the path for a statistics file."""
        return self.run_dir / f"{name}.stats"

    def get_cache_dir(self, name: str) -> Path:
        """Returns the path for a cache subdirectory."""
        d = self.run_dir / f"cache_{name}"
        d.mkdir(exist_ok=True)
        return d

    def get_custom_path(self, *parts) -> Path:
        """Returns an arbitrary path inside the run_dir."""
        p = self.run_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def path(self) -> Path:
        return self.run_dir
