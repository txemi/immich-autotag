import os
from datetime import datetime
from pathlib import Path

from typeguard import typechecked

_RUN_OUTPUT_DIR = None


@typechecked
def get_run_output_dir(base_dir="logs") -> Path:
    global _RUN_OUTPUT_DIR
    if _RUN_OUTPUT_DIR is None:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = os.getpid()
        _RUN_OUTPUT_DIR = Path(base_dir) / f"{now}_PID{pid}"
        _RUN_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return _RUN_OUTPUT_DIR
