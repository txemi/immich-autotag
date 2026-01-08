"""
statistics_checkpoint.py

Utility to obtain the counter of the previous execution (skip_n) from run_statistics.yaml in the previous logs directory.
"""

from pathlib import Path
from typing import Optional

import yaml
from typeguard import typechecked

from immich_autotag.utils.run_output_dir import get_previous_run_output_dir


@typechecked
def get_previous_skip_n(overlap: int = 100) -> Optional[int]:
    """
    Looks for the previous run's run_statistics.yaml and returns the count minus the overlap.
    Returns None if not found.
    """
    prev_dir = get_previous_run_output_dir()
    if prev_dir is None:
        return None
    stats_path = prev_dir / "run_statistics.yaml"
    if not stats_path.exists():
        return None
    with open(stats_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    count = data.get("count", 0)
    skip_n = max(0, count - overlap)
    return skip_n
