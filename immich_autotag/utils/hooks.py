"""
Centralized setup for all runtime hooks: typeguard, architecture import rules, logging, profiling, etc.
Call setup_all_hooks() at the top of your entrypoint before importing any business logic.
"""


def setup_all_hooks() -> None:
    # 1. Typeguard import hook
    from immich_autotag.utils.typeguard_hook import install_typeguard_import_hook

    install_typeguard_import_hook()

    # 2. Architecture import hook
    from immich_autotag.utils.import_architecture_hook import (
        setup_import_architecture_hook,
    )

    setup_import_architecture_hook()

    # 3. Logging and exceptions
    from immich_autotag.utils.setup_runtime import setup_logging_and_exceptions

    setup_logging_and_exceptions()

    # 4. Profiling (optional, for run_main)
    # from immich_autotag.entrypoints.profiling_utils import setup_profiling_and_memory
    # setup_profiling_and_memory()  # Only if you want profiling always enabled
