import atexit
import datetime
import os
import tracemalloc

from immich_autotag.utils.run_output_dir import get_run_output_dir


def setup_tracemalloc_snapshot():
    """
    Set up tracemalloc to track memory allocations and save a snapshot at exit.
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

    atexit.register(_save_snapshot)
