import atexit
import cProfile
import datetime
import os

from immich_autotag.run_output.manager import RunOutputManager


def setup_cprofile_profiler():
    """
    Set up cProfile profiler and register atexit handler to save stats on exit.
    """
    profiler = cProfile.Profile()
    profiler.enable()

    def _save_profile():
        profiler.disable()
        run_dir = RunOutputManager.get_run_output_dir()
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        pid = os.getpid()
        profile_path = run_dir / f"profile_{ts}_PID{pid}.stats"
        profiler.dump_stats(str(profile_path))
        print(f"[PROFILE] cProfile stats saved to {profile_path}")

    atexit.register(_save_profile)
