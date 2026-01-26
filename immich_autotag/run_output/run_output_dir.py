import warnings
from pathlib import Path

from .manager import RunOutputManager

warnings.warn(
    "El módulo run_output_dir.py está deprecado. Usa RunOutputManager en su lugar.",
    DeprecationWarning,
    stacklevel=2,
)


def get_run_output_dir(base_dir: Path | None = None) -> Path:
    return RunOutputManager.get_run_output_dir(base_dir)


def find_recent_run_dirs(
    logs_dir: Path, max_age_hours: int = 3, exclude_current: bool = True
) -> list[Path]:
    return RunOutputManager.find_recent_run_dirs(
        logs_dir, max_age_hours, exclude_current
    )


def get_previous_run_output_dir(base_dir: Path = None) -> Path | None:
    return RunOutputManager.get_previous_run_output_dir(base_dir)
