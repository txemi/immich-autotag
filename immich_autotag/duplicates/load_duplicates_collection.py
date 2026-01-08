from __future__ import annotations

from immich_client import Client
from typeguard import typechecked
from immich_autotag.duplicates.duplicate_collection_wrapper import DuplicateCollectionWrapper
from immich_autotag.duplicates.duplicates_loader import DuplicatesLoader
from immich_autotag.utils.run_output_dir import get_run_output_dir, get_previous_run_output_dir

@typechecked
def load_duplicates_collection(client: Client) -> DuplicateCollectionWrapper:
    """
    Loads the duplicate collection from the Immich server and prints timing information.
    """
    import os
    import pickle
    import time
    from datetime import datetime, timedelta

    # Buscar la caché en el directorio de la ejecución previa
    prev_dir = get_previous_run_output_dir()
    cache_fresh_hours = 3
    duplicates_collection = None
    cache_path = None
    if prev_dir is not None:
        prev_cache = prev_dir / "duplicates_cache.pkl"
        if prev_cache.exists():
            mtime = datetime.fromtimestamp(os.path.getmtime(prev_cache))
            if datetime.now() - mtime < timedelta(hours=cache_fresh_hours):
                with open(prev_cache, "rb") as f:
                    duplicates_collection = pickle.load(f)
                cache_path = prev_cache
                print(f"[INFO] Loaded duplicates from previous run cache ({prev_cache})")

    # Si no hay caché previa válida, usar la carpeta actual
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
        # Guardar la caché en el directorio de la ejecución actual
        cache_path = get_run_output_dir() / "duplicates_cache.pkl"
        with open(cache_path, "wb") as f:
            pickle.dump(duplicates_collection, f)
        print(f"[INFO] Duplicates cached to {cache_path}")

    return duplicates_collection
