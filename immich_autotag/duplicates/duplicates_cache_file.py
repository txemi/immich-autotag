import attr
from typeguard import typechecked
from pathlib import Path
from datetime import datetime
from immich_autotag.duplicates.duplicates_cache_constants import DUPLICATES_CACHE_FILENAME

@typechecked
@attr.s(auto_attribs=True, slots=True, kw_only=True)
class DuplicatesCacheFile:
    directory: Path = attr.ib(validator=attr.validators.instance_of(Path))
    path: Path = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.path = self.directory / DUPLICATES_CACHE_FILENAME

    def exists(self) -> bool:
        return self.path.exists()

    def mtime(self) -> datetime:
        if not self.exists():
            raise FileNotFoundError(f"Cache file does not exist: {self.path}")
        return datetime.fromtimestamp(self.path.stat().st_mtime)

    def age_hours(self, now: datetime | None = None) -> float:
        if not self.exists():
            raise FileNotFoundError(f"Cache file does not exist: {self.path}")
        now = now or datetime.now()
        mtime = self.mtime()
        return (now - mtime).total_seconds() / 3600.0

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return f"<DuplicatesCacheFile path={self.path}>"
