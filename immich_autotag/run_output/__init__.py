"""
run_output package: centralized management of run output paths and data
-----------------------------------------------------------------------

This package groups all logic related to the management of folders, paths, and persistence of outputs
(logs, statistics, caches, reports, etc.) for system runs.

Motivation: avoid logic duplication and dispersion, improve traceability and evolution of the output structure,
and enable robust, coherent post-mortem analysis and cleanup of previous runs.

Contains:
- RunOutputManager: main class to interact with the outputs of a specific run.
- run_output_dir.py: utilities to locate and list previous runs.
"""

from .manager import RunOutputManager
