from datetime import datetime
from pathlib import Path

import attr
from typeguard import typechecked

from immich_autotag.duplicates.duplicates_cache_constants import (
    DUPLICATES_CACHE_FILENAME,
)


@attr.s(auto_attribs=True, slots=True, kw_only=True)
class DuplicatesCacheFile:
    directory: Path = attr.ib(validator=attr.validators.instance_of(Path))
    path: Path = attr.ib(init=False)

    @typechecked
    def __attrs_post_init__(self):
        self.path = self.directory / DUPLICATES_CACHE_FILENAME

    @typechecked
    def exists(self) -> bool:
        return self.path.exists()

    @typechecked
    def mtime(self) -> datetime:
        if not self.exists():
            raise FileNotFoundError(f"Cache file does not exist: {self.path}")
        return datetime.fromtimestamp(self.path.stat().st_mtime)

    @typechecked
    def age_hours(self, now: datetime | None = None) -> float:
        if not self.exists():
            raise FileNotFoundError(f"Cache file does not exist: {self.path}")
        now = now or datetime.now()
        mtime = self.mtime()
        return (now - mtime).total_seconds() / 3600.0

    @typechecked
    def __str__(self):
        return str(self.path)

    @typechecked
    def __repr__(self):
        return f"<DuplicatesCacheFile path={self.path}>"

    @property
    @typechecked
    def dir_mtime(self) -> datetime:
        return datetime.fromtimestamp(self.directory.stat().st_mtime)

    @property
    @typechecked
    def dir_age_hours(self) -> float:
        return (datetime.now() - self.dir_mtime).total_seconds() / 3600.0

    @typechecked
    def status_string(self) -> str:
        try:
            if self.exists():
                file_age = self.age_hours()
                return f"{self.directory.name} (dir_age={self.dir_age_hours:.2f}h, cache_age={file_age:.2f}h, found=YES)"
            else:
                return f"{self.directory.name} (dir_age={self.dir_age_hours:.2f}h, found=NO)"
        except Exception:
            return f"{self.directory} (error checking stats)"

    @typechecked
    def is_fresh(self, max_age_hours: float) -> bool:
        """Return True if the cache file is newer than the given threshold in hours."""
        return self.age_hours_from() < max_age_hours

    @typechecked
    def age_hours_from(self, now: datetime | None = None) -> float:
        """Return the age in hours from now (or a given datetime) to the file's mtime."""
        if now is None:
            now = datetime.now()
        return (now - self.mtime()).total_seconds() / 3600.0
