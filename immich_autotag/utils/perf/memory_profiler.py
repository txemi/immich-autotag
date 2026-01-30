import atexit
import os
import threading
import time
import tracemalloc

from immich_autotag.run_output.manager import RunOutputManager


def setup_tracemalloc_snapshot():
    """
    Set up tracemalloc to track memory allocations and save a snapshot at exit and
    periodically.
    """
    tracemalloc.start()

    def _save_snapshot():
        snapshot = tracemalloc.take_snapshot()
        run_exec = RunOutputManager.current().get_run_output_dir()
        snapshot_path = run_exec.get_tracemalloc_snapshot_path()
        snapshot.dump(str(snapshot_path))
        print(f"[MEMORY] tracemalloc snapshot saved to {snapshot_path}")

    # Register atexit handler for final snapshot
    atexit.register(_save_snapshot)

    # Periodic snapshotting
    interval = float(
        os.environ.get("TRACEMALLOC_SNAPSHOT_INTERVAL", 300)
    )  # seconds, default 5 min
    stop_event = threading.Event()

    def periodic_snapshots():
        while not stop_event.is_set():
            time.sleep(interval)
            try:
                _save_snapshot()
            except Exception as e:
                print(f"[MEMORY] Error saving periodic tracemalloc snapshot: {e}")

    t = threading.Thread(target=periodic_snapshots, daemon=True)
    t.start()
