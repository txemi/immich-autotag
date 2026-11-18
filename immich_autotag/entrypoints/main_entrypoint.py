from __future__ import annotations

import sys

# Centralized hook setup: ensures all runtime hooks are installed before importing business logic.
from immich_autotag.utils.hooks import setup_all_hooks

setup_all_hooks()


# Import main logic after hooks are active (required for typeguard, architecture, etc.)
# noqa: E402 justified: Hooks must be installed before any business logic is imported, to guarantee runtime checks and architecture enforcement. This is a deliberate and documented exception.
from immich_autotag.entrypoints.main_logic import run_main_inner_logic  # noqa: E402

# Profiling utils (for run_main)
from immich_autotag.entrypoints.profiling_utils import (  # noqa: E402
    setup_profiling_and_memory,
)


def run_main():
    """
    Wrapper that runs run_main_inner, and if error mode is CRAZY_DEBUG, activates cProfile and saves the result in profile_debug.stats.
    """
    setup_profiling_and_memory()
    from immich_autotag.dry_run.dry_run_session import finish_current_session

    completed = False
    try:
        run_main_inner_logic()
        completed = True
    finally:
        # In a dry run, the summary is written even when the run fails. A failure
        # writing it must not hide the pipeline's own error.
        try:
            finish_current_session(completed=completed)
        except Exception as error:  # noqa: BLE001
            if completed:
                raise
            print(f"[dry-run] could not write the summary: {error!r}", file=sys.stderr)
