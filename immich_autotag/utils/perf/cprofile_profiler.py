def setup_cprofile_profiler():
    """
    Set up cProfile profiler and register atexit handler to save stats on exit and periodically.
    """
    import atexit
    import cProfile
    import os
    import threading
    import time

    from immich_autotag.run_output.manager import RunOutputManager

    profiler = cProfile.Profile()
    profiler.enable()

    def _save_profile():
        profiler.disable()
        run_exec = RunOutputManager.current().get_run_output_dir()
        profile_path = run_exec.get_cprofile_stats_path()
        profiler.dump_stats(str(profile_path))
        print(f"[PROFILE] cProfile stats saved to {profile_path}")

    atexit.register(_save_profile)

    # Periodic saving
    interval = float(
        os.environ.get("CPROFILE_SNAPSHOT_INTERVAL", 300)
    )  # seconds, default 5 min
    stop_event = threading.Event()

    def periodic_profile_snapshots():
        while not stop_event.is_set():
            time.sleep(interval)
            try:
                # Save snapshot without stopping the profiler
                run_exec = RunOutputManager.current().get_run_output_dir()
                profile_path = run_exec.get_cprofile_stats_path()
                profiler.dump_stats(str(profile_path))
                print(f"[PROFILE] Periodic cProfile stats saved to {profile_path}")
            except Exception as e:
                print(f"[PROFILE] Error saving periodic cProfile stats: {e}")

    t = threading.Thread(target=periodic_profile_snapshots, daemon=True)
    t.start()
