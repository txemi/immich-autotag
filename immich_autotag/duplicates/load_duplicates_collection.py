from __future__ import annotations

from typeguard import typechecked

from immich_autotag.duplicates._find_recent_duplicates_cache import (
    find_recent_duplicates_cache,
)
from immich_autotag.duplicates._load_cache import load_cache
from immich_autotag.duplicates.duplicate_collection_wrapper import (
    DuplicateCollectionWrapper,
)
from immich_autotag.duplicates.duplicates_cache_file import DuplicatesCacheFile
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
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(f"Loaded duplicates from cache ({cache_path})", level=LogLevel.INFO)
    if duplicates_collection is None:
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            "Requesting duplicates from Immich server... (this may take a while)",
            level=LogLevel.INFO,
        )
        t0 = time.perf_counter()
        duplicates_loader = DuplicatesLoader(client=client)
        duplicates_collection = duplicates_loader.load()
        t1 = time.perf_counter()
        log(
            f"Duplicates loaded in {t1-t0:.2f} s. Total groups: {len(duplicates_collection.groups_by_duplicate_id)}",
            level=LogLevel.INFO,
        )
        # Save the cache in the current execution directory.
        # Avoid writing extremely large caches in CI or when the collection is huge.
        cache_file = DuplicatesCacheFile(directory=get_run_output_dir())
        cache_path = cache_file.path
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
        # Thresholds (tunable): if exceeded, skip writing the full pickle to avoid huge files.
        # Increased thresholds to ensure cache is written for typical user libraries
        GROUPS_THRESHOLD = 500000
        ASSETS_THRESHOLD = 1000000

        if (0 <= total_groups <= GROUPS_THRESHOLD) and (
            0 <= total_assets <= ASSETS_THRESHOLD
        ):
            with open(cache_path, "wb") as f:
                pickle.dump(duplicates_collection, f)
            log(
                f"Duplicates cached to {cache_path} (groups={total_groups}, assets={total_assets})",
                level=LogLevel.INFO,
            )
        else:
            # Instead of serializing the full collection, write a small summary file
            # containing counts and a limited sample of group ids to help diagnostics.
            try:
                import json

                sample_limit = 100
                sample_group_ids = list(
                    duplicates_collection.groups_by_duplicate_id.keys()
                )[:sample_limit]
                summary = {
                    "groups": total_groups,
                    "assets": total_assets,
                    "sample_group_ids": sample_group_ids,
                }
                summary_path = cache_path.with_suffix(".summary.json")
                with open(summary_path, "w", encoding="utf-8") as sf:
                    json.dump(summary, sf, ensure_ascii=False)
                log(
                    f"Skipped full duplicates pickle (too large). Wrote summary to {summary_path}",
                    level=LogLevel.INFO,
                )
            except Exception:
                log(
                    f"Skipping caching duplicates to {cache_path} because collection is large "
                    f"(groups={total_groups}, assets={total_assets}). Set a higher threshold if you need caching.",
                    level=LogLevel.INFO,
                )
    return duplicates_collection
