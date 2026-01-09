import pickle
from pathlib import Path
from typing import Optional

from typeguard import typechecked

from immich_autotag.duplicates.duplicate_collection_wrapper import (
    DuplicateCollectionWrapper,
)


@typechecked
def load_cache(cache_path: Path) -> Optional[DuplicateCollectionWrapper]:
    """
    Intenta cargar el cache de duplicados desde el fichero dado.
    Devuelve el objeto o None si falla.
    """
    try:
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"[WARN] Could not load duplicates cache {cache_path}: {e}")
        return None
