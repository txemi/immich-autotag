import atexit
import cProfile

from immich_autotag.run_output.manager import RunOutputManager


def setup_cprofile_profiler():
    """
    Set up cProfile profiler and register atexit handler to save stats on exit.
    """
    profiler = cProfile.Profile()
    profiler.enable()

    def _save_profile():
        profiler.disable()
        run_exec = RunOutputManager.current().get_run_output_dir()
        profile_path = run_exec.get_cprofile_stats_path()
        profiler.dump_stats(str(profile_path))
        print(f"[PROFILE] cProfile stats saved to {profile_path}")

    atexit.register(_save_profile)
