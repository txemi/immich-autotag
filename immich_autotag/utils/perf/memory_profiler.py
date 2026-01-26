
import atexit
import tracemalloc
import datetime
import os
import threading
import time
from immich_autotag.utils.run_output_dir import get_run_output_dir

def setup_tracemalloc_snapshot():
    """
    Set up tracemalloc to track memory allocations and save a snapshot at exit and periodically.
    """
    tracemalloc.start()

    def _save_snapshot():
        snapshot = tracemalloc.take_snapshot()
        run_dir = get_run_output_dir()
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        pid = os.getpid()
        snapshot_path = run_dir / f"tracemalloc_{ts}_PID{pid}.dat"
        snapshot.dump(str(snapshot_path))
        print(f"[MEMORY] tracemalloc snapshot saved to {snapshot_path}")

    # Register atexit handler for final snapshot
    atexit.register(_save_snapshot)

    # Periodic snapshotting
    interval = float(os.environ.get("TRACEMALLOC_SNAPSHOT_INTERVAL", 300))  # seconds, default 5 min
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
