from pathlib import Path
from typing import Optional
import os
from datetime import datetime

class RunOutputManager:
    """
    Encapsula la lógica de rutas y persistencia de outputs para una ejecución concreta.
    Permite a los subsistemas pedir rutas para logs, estadísticas, cachés, informes, etc.
    También permite instanciarse sobre ejecuciones anteriores para buscar datos históricos.
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
