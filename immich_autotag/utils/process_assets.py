import time
from threading import Lock
from immich_autotag.core.tag_modification_report import TagModificationReport
from immich_autotag.utils.process_single_asset import process_single_asset
from immich_autotag.utils.get_all_assets import get_all_assets
from immich_autotag.utils.helpers import print_perf
from immich_autotag.config import MAX_WORKERS, USE_THREADPOOL

def process_assets(context, max_assets: int | None = None) -> None:
    from immich_client.api.server import get_server_statistics

    tag_mod_report = TagModificationReport()
    lock = Lock()
    count = 0
    N_LOG = 100  # Log frequency
    print(
        f"Processing assets with MAX_WORKERS={MAX_WORKERS}, USE_THREADPOOL={USE_THREADPOOL}..."
    )
    # Get total assets before processing
    try:
        stats = get_server_statistics.sync(client=context.client)
        total_assets = getattr(stats, "photos", 0) + getattr(stats, "videos", 0)
        print(
            f"[INFO] Total assets (photos + videos) reported by Immich: {total_assets}"
        )
    except Exception as e:
        print(f"[WARN] Could not get total assets from API: {e}")
        total_assets = None
    start_time = time.time()

    if USE_THREADPOOL:
        # Use thread pool regardless of MAX_WORKERS value
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for asset_wrapper in get_all_assets(context, max_assets=max_assets):
                future = executor.submit(
                    process_single_asset, asset_wrapper, tag_mod_report, lock
                )
                futures.append(future)
                count += 1
                if count % N_LOG == 0:
                    elapsed = time.time() - start_time
                    print_perf(count, elapsed)
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[ERROR] Asset processing failed: {e}")
    else:
        # Direct loop (sequential), no thread pool
        for asset_wrapper in get_all_assets(context, max_assets=max_assets):
            process_single_asset(asset_wrapper, tag_mod_report, lock)
            count += 1
            if count % N_LOG == 0:
                elapsed = time.time() - start_time
                print_perf(count, elapsed)
    total_time = time.time() - start_time
    print(f"Total assets: {count}")
    print(
        f"[PERF] Tiempo total: {total_time:.2f} s. Media por asset: {total_time/count if count else 0:.3f} s"
    )
    if len(tag_mod_report.modifications) > 0:
        tag_mod_report.print_summary()
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the real minimum number of assets
    if count < MIN_ASSETS:
        raise Exception(
            f"ERROR: Unexpectedly low number of assets: {count} < {MIN_ASSETS}"
        )
