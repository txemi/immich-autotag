from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import attr
import attrs


def _validate_is_dir(
    instance: Any, attribute: attr.Attribute[Path], value: Path
) -> None:
    if not value.is_dir():
        raise ValueError(f"{attribute.name} must be a directory: {value}")


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class RecentRunDir:
    _subdir: Path = attrs.field(
        validator=[attrs.validators.instance_of(Path), _validate_is_dir]
    )

    def get_datetime(self: "RecentRunDir") -> Optional[datetime]:
        """Extracts the datetime from the subdir name."""
        from .manager import RunOutputManager

        try:
            dt_str = self._subdir.name.split(RunOutputManager.get_run_dir_pid_sep())[0]
            return datetime.strptime(dt_str, RunOutputManager.get_run_dir_date_format())
        except Exception:
            return None

    def get_path(self: "RecentRunDir") -> Path:
        """Returns the path of the run directory."""
        return self._subdir

    def is_recent(self: "RecentRunDir", now: datetime, max_age_hours: int) -> bool:
        dt = self.get_datetime()
        return dt is not None and now - dt < timedelta(hours=max_age_hours)

    @classmethod
    def from_path(cls: type["RecentRunDir"], subdir: Path) -> Optional["RecentRunDir"]:
        from .manager import RunOutputManager

        if (
            not subdir.is_dir()
            or RunOutputManager.get_run_dir_pid_mark() not in subdir.name
        ):
            return None
        return cls(_subdir=subdir)
