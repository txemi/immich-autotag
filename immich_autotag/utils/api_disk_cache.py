import json
from pathlib import Path
from typing import Optional

from immich_autotag.utils.run_output_dir import find_recent_run_dirs, get_run_output_dir

# Config global para activar/desactivar cacheo (puede ser sobrescrito por parámetro)
API_CACHE_ENABLED = True

CACHE_SUBDIR = "api_cache"


def _get_cache_dir(entity: str, run_dir: Optional[Path] = None) -> Path:
    """Devuelve el directorio de caché para una entidad (albums, assets, etc) en la ejecución dada."""
    if run_dir is None:
        run_dir = get_run_output_dir()
    cache_dir = run_dir / CACHE_SUBDIR / entity
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def save_entity_to_cache(entity: str, key: str, data: dict) -> None:
    """Guarda un objeto en la caché de la ejecución actual."""
    cache_dir = _get_cache_dir(entity)
    path = cache_dir / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_entity_from_cache(
    entity: str, key: str, use_cache: Optional[bool] = None
) -> Optional[dict]:
    """
    Busca un objeto en la caché (primero en la ejecución actual, luego en previas).
    Si use_cache es False, nunca busca en caché.
    """
    if use_cache is None:
        use_cache = API_CACHE_ENABLED
    if not use_cache:
        return None
    # 1. Buscar en la ejecución actual
    cache_dir = _get_cache_dir(entity)
    path = cache_dir / f"{key}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 2. Buscar en ejecuciones previas (ordenadas de más reciente a más antigua)
    logs_dir = Path("logs_local")
    for run_dir in find_recent_run_dirs(logs_dir, exclude_current=True):
        prev_cache_dir = run_dir / CACHE_SUBDIR / entity
        prev_path = prev_cache_dir / f"{key}.json"
        if prev_path.exists():
            with open(prev_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Opcional: copiar a la caché actual para acelerar futuras búsquedas
            save_entity_to_cache(entity, key, data)
            return data
    return None
