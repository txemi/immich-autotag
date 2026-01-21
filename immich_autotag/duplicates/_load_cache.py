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
    Attempts to load the duplicates cache from the given file.
    Returns the object or None if it fails.
    """
    try:
        with open(cache_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            f"Could not load duplicates cache {cache_path}: {e}", level=LogLevel.WARNING
        )
        return None
