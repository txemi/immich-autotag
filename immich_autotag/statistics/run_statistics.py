from typeguard import typechecked

"""
run_statistics.py

Data model for execution statistics, serializable to YAML.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field


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
    git_version: Optional[str] = Field(
        None, description="Git version/tag of the code executed (from git describe)"
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

    @typechecked
    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.model_dump(),
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    @classmethod
    @typechecked
    def from_yaml(cls, data: str) -> "RunStatistics":
        return cls.model_validate(yaml.safe_load(data))
