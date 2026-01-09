from __future__ import annotations

from immich_client import Client
from typeguard import typechecked

from immich_autotag.duplicates._find_recent_duplicates_cache import (
    find_recent_duplicates_cache,
)
from immich_autotag.duplicates._load_cache import load_cache
from immich_autotag.duplicates.duplicate_collection_wrapper import (
    DuplicateCollectionWrapper,
)
from immich_autotag.duplicates.duplicates_loader import DuplicatesLoader
from immich_autotag.utils.run_output_dir import get_run_output_dir


@typechecked
def load_duplicates_collection(client: Client) -> DuplicateCollectionWrapper:
    """
    Loads the duplicate collection from the Immich server and prints timing information.
    """
    import time
    from pathlib import Path

    cache_fresh_hours = 3
    logs_dir = Path("logs")
    cache_path = find_recent_duplicates_cache(logs_dir, cache_fresh_hours)
    duplicates_collection = None
    if cache_path:
        duplicates_collection = load_cache(cache_path)
        if duplicates_collection:
            print(f"[INFO] Loaded duplicates from cache ({cache_path})")
    if duplicates_collection is None:
        print(
            "[INFO] Requesting duplicates from Immich server... (this may take a while)"
        )
        t0 = time.perf_counter()
        duplicates_loader = DuplicatesLoader(client=client)
        duplicates_collection = duplicates_loader.load()
        t1 = time.perf_counter()
        print(
            f"[INFO] Duplicates loaded in {t1-t0:.2f} s. Total groups: {len(duplicates_collection.groups_by_duplicate_id)}"
        )
        # Save the cache in the current execution directory
        cache_path = get_run_output_dir() / "duplicates_cache.pkl"
        import pickle

        with open(cache_path, "wb") as f:
            pickle.dump(duplicates_collection, f)
        print(f"[INFO] Duplicates cached to {cache_path}")
    return duplicates_collection
