from __future__ import annotations

from typeguard import typechecked

from immich_autotag.duplicates._find_recent_duplicates_cache import (
    find_recent_duplicates_cache,
)
from immich_autotag.duplicates._load_cache import load_cache
from immich_autotag.duplicates.duplicate_collection_wrapper import (
    DuplicateCollectionWrapper,
)
from immich_autotag.duplicates.duplicates_loader import DuplicatesLoader
from immich_autotag.types import ImmichClient
from immich_autotag.utils.run_output_dir import get_run_output_dir


@typechecked
def load_duplicates_collection(client: ImmichClient) -> DuplicateCollectionWrapper:
    """
    Loads the duplicate collection from the Immich server and prints timing information.
    """
    import time

    cache_fresh_hours = 3
    from immich_autotag.utils.run_output_dir import LOGS_LOCAL_DIR

    logs_dir = LOGS_LOCAL_DIR
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
        # Save the cache in the current execution directory.
        # Avoid writing extremely large caches in CI or when the collection is huge.
        cache_path = get_run_output_dir() / "duplicates_cache.pkl"
        import pickle

        try:
            # Estimate size by counting groups and assets; avoid full serialization if huge.
            total_groups = len(duplicates_collection.groups_by_duplicate_id)
            total_assets = sum(
                len(g.assets)
                for g in duplicates_collection.groups_by_duplicate_id.values()
            )
        except Exception:
            total_groups = -1
            total_assets = -1

        # Thresholds (tunable): if exceeded, skip writing the full pickle to avoid huge files.
        GROUPS_THRESHOLD = 5000
        ASSETS_THRESHOLD = 100000

        if (0 <= total_groups <= GROUPS_THRESHOLD) and (
            0 <= total_assets <= ASSETS_THRESHOLD
        ):
            with open(cache_path, "wb") as f:
                pickle.dump(duplicates_collection, f)
            print(
                f"[INFO] Duplicates cached to {cache_path} (groups={total_groups}, assets={total_assets})"
            )
        else:
            print(
                f"[INFO] Skipping caching duplicates to {cache_path} because collection is large "
                f"(groups={total_groups}, assets={total_assets}). Set a higher threshold if you need caching."
            )
    return duplicates_collection
