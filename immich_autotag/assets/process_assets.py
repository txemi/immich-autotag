"""
Legacy import module for backward compatibility.
All functions have been moved to their respective modules in the process/ subdirectory.
This file provides imports from the new locations.
"""

from __future__ import annotations

# Import from new locations for backward compatibility
from immich_autotag.assets.process.fetch_total_assets import fetch_total_assets
from immich_autotag.assets.process.log_execution_parameters import (
    log_execution_parameters,
)
from immich_autotag.assets.process.log_final_summary import log_final_summary
from immich_autotag.assets.process.perf_log import perf_log
from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.assets.process.process_assets_sequential import (
    process_assets_sequential,
)
from immich_autotag.assets.process.process_assets_threadpool import (
    process_assets_threadpool,
)
from immich_autotag.assets.process.register_execution_parameters import (
    register_execution_parameters,
)
from immich_autotag.assets.process.resolve_checkpoint import resolve_checkpoint

# Re-export all symbols for backward compatibility
__all__ = [
    "log_execution_parameters",
    "fetch_total_assets",
    "resolve_checkpoint",
    "register_execution_parameters",
    "perf_log",
    "process_assets_threadpool",
    "process_assets_sequential",
    "log_final_summary",
    "process_assets",
]
