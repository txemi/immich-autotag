"""
statistics_checkpoint.py

Utilidad para obtener el contador de la última ejecución previa (skip_n) a partir de run_statistics.yaml en el directorio de logs anterior.
"""

from pathlib import Path
from typing import Optional

import yaml

from immich_autotag.utils.run_output_dir import get_previous_run_output_dir


def get_previous_skip_n(overlap: int = 100) -> Optional[int]:
    """
    Busca el run_statistics.yaml de la ejecución previa y devuelve el contador count menos el solapamiento (overlap).
    Si no existe, devuelve None.
    """
    prev_dir = get_previous_run_output_dir()
    if prev_dir is None:
        return None
    stats_path = prev_dir / "run_statistics.yaml"
    if not stats_path.exists():
        return None
    with open(stats_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    count = data.get("count", 0)
    skip_n = max(0, count - overlap)
    return skip_n
