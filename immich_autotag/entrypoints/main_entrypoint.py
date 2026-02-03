from __future__ import annotations

# 1. Typeguard import hook must be installed before any other imports!
from immich_autotag.utils.typeguard_hook import (
    install_typeguard_import_hook,
)  # isort: skip

# 2. Architecture import hook (for import restrictions)
from immich_autotag.utils.import_architecture_hook import setup_import_architecture_hook

# 3. Setup logging and exceptions
from immich_autotag.utils.setup_runtime import setup_logging_and_exceptions

# 4. Import main logic (now hooks are active)
from immich_autotag.entrypoints.main_logic import run_main_inner_logic

# 5. Profiling utils (for run_main)
from immich_autotag.entrypoints.profiling_utils import setup_profiling_and_memory

install_typeguard_import_hook()
setup_import_architecture_hook()
setup_logging_and_exceptions()


def run_main_inner() -> None:

    run_main_inner_logic()


def run_main():
    """
    Wrapper that runs run_main_inner, and if error mode is CRAZY_DEBUG, activates cProfile and saves the result in profile_debug.stats.
    """
    setup_profiling_and_memory()
    run_main_inner()
