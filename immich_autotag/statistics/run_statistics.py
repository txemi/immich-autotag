from typeguard import typechecked

from immich_autotag.statistics.constants import RUN_STATISTICS_FILENAME

"""
run_statistics.py

Data model for execution statistics, serializable to YAML.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

from immich_autotag.tags.modification_kind import ModificationKind
from immich_autotag.tags.tag_response_wrapper import TagWrapper


# Strict typing for output tag counters
class OutputTagCounter(BaseModel):
    total: int = 0
    added: int = 0
    removed: int = 0
    errors: int = 0  # New: count errors for this tag


# Strict typing for output album counters
class OutputAlbumCounter(BaseModel):
    total: int = 0
    assigned: int = 0
    removed: int = 0
    errors: int = 0


class RunStatistics(BaseModel):

    git_describe_runtime: Optional[str] = Field(
        None,
        description="Git describe string obtained at runtime (from GitPython, may be empty in containers)",
    )
    git_describe_package: Optional[str] = Field(
        None,
        description="Git describe string from the distributed package (from version.py, always present)",
    )
    album_date_mismatch_count: int = Field(
        0, description="Count of album/date mismatches"
    )

    update_asset_date_count: int = Field(0, description="Number of asset date updates")

    total_assets: Optional[int] = Field(
        None, description="Total elements reported by the system at startup"
    )
    max_assets: Optional[int] = Field(
        None,
        description="Maximum elements to process in this execution (None = all)",
    )
    skip_n: Optional[int] = Field(
        None, description="Number of elements to skip at the beginning (offset)"
    )

    last_processed_id: Optional[str] = Field(
        None, description="ID of the last processed asset"
    )
    count: int = Field(0, description="Number of processed assets")
    started_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    finished_at: Optional[datetime] = None
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="Extensible field for future stats"
    )
    output_tag_counters: Dict[str, OutputTagCounter] = Field(
        default_factory=dict, description="Counters per output tag"
    )
    output_album_counters: Dict[str, OutputAlbumCounter] = Field(
        default_factory=dict, description="Counters per output album"
    )
    progress_description: Optional[str] = Field(
        None,
        description="Textual description of current progress (percentage, estimated time, etc.)",
    )

    # Event counters by type (key: str, value: int)
    event_counters: Dict[str, int] = Field(
        default_factory=dict,
        description="Event counters by ModificationKind (string key)",
    )

    @typechecked
    def increment_event(
        self, event_kind: ModificationKind, extra_key: "TagWrapper | None" = None
    ) -> None:
        """
        Increment the counter for the given event kind (ModificationKind).
        If extra_key (TagWrapper) is provided, it is concatenated to the event_kind name for per-key statistics.
        """
        key = event_kind.name
        if extra_key is not None:
            # Use the tag name
            extra_val = extra_key.get_name()
            key = f"{key}_{extra_val}"
        if key not in self.event_counters:
            self.event_counters[key] = 0
        self.event_counters[key] += 1

    @typechecked
    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.model_dump(),
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "RunStatistics":
        if not isinstance(path, Path):
            raise TypeError(
                f"from_yaml only accepts a Path object as input. Expected file: {RUN_STATISTICS_FILENAME}"
            )
        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path} (expected {RUN_STATISTICS_FILENAME})"
            )
        with path.open("r", encoding="utf-8") as f:
            data = f.read()
        loaded = yaml.safe_load(data)
        if loaded is None:
            # Empty or invalid file: raise an explicit error
            raise ValueError(
                f"{RUN_STATISTICS_FILENAME} is empty or invalid; cannot create RunStatistics instance."
            )
        return cls.model_validate(loaded)

    @typechecked
    def get_total_to_process(self) -> int | None:
        if self.total_assets is None:
            return None
        skip = self.skip_n or 0
        return max(1, self.total_assets - skip)

    @typechecked
    def get_start_time(self) -> float:
        if self.started_at is None:
            raise RuntimeError("RunStatistics.started_at is not set")
        return self.started_at.timestamp()
