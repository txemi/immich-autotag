from __future__ import annotations

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


def run_main_inner() -> None:

    run_main_inner_logic()


def run_main():
    """
    Wrapper that runs run_main_inner, and if error mode is CRAZY_DEBUG, activates cProfile and saves the result in profile_debug.stats.
    """
    setup_profiling_and_memory()
    run_main_inner()
