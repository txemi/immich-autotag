from __future__ import annotations

from typing import TYPE_CHECKING

# Typeguard import hook must be installed before any other imports!
from immich_autotag.utils.typeguard_hook import (  # isort: skip
    install_typeguard_import_hook,
)

install_typeguard_import_hook()  # noqa: E402

# Architecture import hook (for import restrictions)
from immich_autotag.utils.import_architecture_hook import (
    setup_import_architecture_hook,
)

setup_import_architecture_hook()

from immich_autotag.utils.setup_runtime import (  # noqa: E402
    setup_logging_and_exceptions,
)

setup_logging_and_exceptions()

if TYPE_CHECKING:
    pass

from immich_autotag.entrypoints.main_logic import run_main_inner_logic  # noqa: E402


def run_main_inner() -> None:
    run_main_inner_logic()


def run_main():
    """
    Wrapper that runs run_main_inner, and if error mode is CRAZY_DEBUG, activates cProfile and saves the result in profile_debug.stats.
    """
    from immich_autotag.entrypoints.profiling_utils import setup_profiling_and_memory

    setup_profiling_and_memory()
    run_main_inner()
