from pathlib import Path
from typing import Optional
import os
from datetime import datetime

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

    def get_log_path(self, name: str) -> Path:
        """Devuelve la ruta para un log específico de esta ejecución."""
        return self.run_dir / f"{name}.log"

    def get_stats_path(self, name: str) -> Path:
        """Devuelve la ruta para un fichero de estadísticas."""
        return self.run_dir / f"{name}.stats"

    def get_cache_dir(self, name: str) -> Path:
        """Devuelve la ruta para un subdirectorio de caché."""
        d = self.run_dir / f"cache_{name}"
        d.mkdir(exist_ok=True)
        return d

    def get_custom_path(self, *parts) -> Path:
        """Devuelve una ruta arbitraria dentro del run_dir."""
        p = self.run_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def path(self) -> Path:
        return self.run_dir
