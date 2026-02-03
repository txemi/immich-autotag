from __future__ import annotations

# Centralized hook setup: ensures all runtime hooks are installed before importing business logic.
from immich_autotag.utils.hooks import setup_all_hooks

setup_all_hooks()

# Import main logic after hooks are active (required for typeguard, architecture, etc.)
from immich_autotag.entrypoints.main_logic import run_main_inner_logic  # noqa: E402

# Profiling utils (for run_main)
from immich_autotag.entrypoints.profiling_utils import (
    setup_profiling_and_memory,
)  # noqa: E402


def run_main_inner() -> None:

    run_main_inner_logic()


def run_main():
    """
    Wrapper that runs run_main_inner, and if error mode is CRAZY_DEBUG, activates cProfile and saves the result in profile_debug.stats.
    """
    setup_profiling_and_memory()
    run_main_inner()
