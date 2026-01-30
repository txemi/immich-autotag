# New import: RunExecution is in execution.py
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


import attrs
from ._recent_run_dir import RecentRunDir
from .execution import RunExecution

# --- Private module-level constants and variables for execution management ---

_RUN_DIR_PID_MARK = "PID"
_RUN_DIR_PID_SEP = "_PID"
_RUN_DIR_DATE_FORMAT = "%Y%m%d_%H%M%S"
_current_instance = None


@attrs.define(auto_attribs=True, slots=True)
class RunOutputManager:
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

    _run_output_dir: Optional[RunExecution] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(RunExecution)),
    )
    _logs_local_dir: Path = attrs.field(
        default=Path("logs_local"), validator=attrs.validators.instance_of(Path)
    )

    def __attrs_post_init__(self):
        global _current_instance
        if _current_instance is not None:
            raise RuntimeError(
                "RunOutputManager is a singleton. Use RunOutputManager.current() to get the instance."
            )

    @staticmethod
    def get_run_dir_pid_sep() -> str:
        return _RUN_DIR_PID_SEP

    @staticmethod
    def get_run_dir_date_format() -> str:
        return _RUN_DIR_DATE_FORMAT

    @staticmethod
    def get_run_dir_pid_mark() -> str:
        return _RUN_DIR_PID_MARK

    @staticmethod
    def _is_run_dir(subdir: Path) -> bool:
        """
        Returns True if the subfolder is an execution folder (contains _RUN_DIR_PID_MARK in the name).
        """
        return subdir.is_dir() and _RUN_DIR_PID_MARK in subdir.name

    @staticmethod
    def _extract_datetime_from_run_dir(subdir: Path) -> Optional[datetime]:
        """
        Extracts the date from the execution folder (YYYYMMDD_HHMMSS before _RUN_DIR_PID_SEP).
        """
        try:
            dt_str = subdir.name.split(_RUN_DIR_PID_SEP)[0]
            return datetime.strptime(dt_str, _RUN_DIR_DATE_FORMAT)
        except Exception:
            return None

    def _list_run_dirs(self, base_dir: Path) -> list[Path]:
        """Returns all valid execution subfolders in base_dir."""
        return [d for d in base_dir.iterdir() if self._is_run_dir(d)]

    def get_run_output_dir(self) -> RunExecution:
        """
        Returns a RunExecution object for the current run. Argument must be a Path.
        """
        if self._run_output_dir is None:
            base_dir = self._logs_local_dir
            now = datetime.now().strftime(_RUN_DIR_DATE_FORMAT)
            pid = os.getpid()
            run_dir = Path(base_dir) / f"{now}{_RUN_DIR_PID_SEP}{pid}"
            run_dir.mkdir(parents=True, exist_ok=True)
            self._run_output_dir = RunExecution(run_dir)
        return self._run_output_dir

    def find_recent_run_dirs(
        self, max_age_hours: int = 3, exclude_current: bool = True
    ) -> list["RunExecution"]:
        """
        Returns a list of RunExecution objects for recent executions (subfolders with 'PID' in the name and valid date),
        ordered from most recent to oldest, filtered by age (max_age_hours).
        If exclude_current is True, excludes the current execution folder.
        """
        logs_dir = self._logs_local_dir
        now = datetime.now()
        current_run = self.get_run_output_dir() if exclude_current else None
        current_run_dir = current_run.path if current_run else None
        recent_dirs: list[RecentRunDir] = []
        for subdir in self._list_run_dirs(logs_dir):
            if exclude_current and subdir.resolve() == current_run_dir:
                continue
            rrd = RecentRunDir.from_path(subdir)
            if rrd is not None and rrd.is_recent(now, max_age_hours):
                recent_dirs.append(rrd)
        recent_dirs.sort(key=lambda r: r.get_datetime() or datetime.min, reverse=True)
        return [RunExecution(r.get_path()) for r in recent_dirs]

    def get_previous_run_output_dir(self) -> Optional[RunExecution]:
        """
        Searches for the most recent previous execution folder in the default logs directory.
        Returns Path or None if there are no previous executions.
        """
        base = self._logs_local_dir
        if not base.exists() or not base.is_dir():
            raise RuntimeError(
                f"Logs directory does not exist or is not a directory: {base}"
            )
        dirs = self._list_run_dirs(base)
        if not dirs:
            raise RuntimeError(f"No run directories found in logs directory: {base}")
        current = self.get_run_output_dir()
        dirs.sort(
            key=lambda d: self._extract_datetime_from_run_dir(d) or datetime.min,
            reverse=True,
        )
        for d in dirs:
            if d != current.path:
                return RunExecution(d)
        # No previous run directory found; returning None is expected and not an error.
        return None

    @staticmethod
    def current() -> "RunOutputManager":
        """
        Returns the singleton instance associated with the current execution.
        If it does not exist, it creates it.
        """
        global _current_instance
        if _current_instance is None:
            _current_instance = RunOutputManager()
        return _current_instance

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

    def get_custom_path(self, *parts: str) -> Path:
        """Returns an arbitrary path inside the run_dir."""
        p = self.run_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def path(self) -> Path:
        return self.run_dir
