"""
models.py

Pydantic models for the new structured configuration (experimental).
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    host: str
    port: int
    api_key: str


# Unified classification rule: can be by tag_names or album_name_patterns
from typing import Optional


class ClassificationRule(BaseModel):
    tag_names: Optional[List[str]] = None
    album_name_patterns: Optional[List[str]] = None
    asset_links: Optional[List[str]] = None


class FilterConfig(BaseModel):
    filter_in: List[ClassificationRule] = Field(default_factory=list)
    filter_out: List[ClassificationRule] = Field(default_factory=list)


class Conversion(BaseModel):
    source: ClassificationRule
    destination: ClassificationRule


class ClassificationConfig(BaseModel):
    rules: List[ClassificationRule] = Field(default_factory=list)
    autotag_unknown: Optional[str] = None
    autotag_conflict: Optional[str] = None


class DateCorrectionConfig(BaseModel):
    enabled: bool
    extraction_timezone: str


class DuplicateProcessingConfig(BaseModel):
    autotag_album_date_mismatch: str = Field(
        default="autotag_output_album_date_mismatch",
        description="Tag for album/asset date mismatch. Used if not specified by user.",
    )

    autotag_album_conflict: Optional[str] = None
    autotag_classification_conflict: Optional[str] = None
    autotag_classification_conflict_prefix: Optional[str] = None
    autotag_album_detection_conflict: Optional[str] = None
    date_correction: DateCorrectionConfig


# Grouping of coupled fields in subclasses
class AlbumDetectionFromFoldersConfig(BaseModel):
    enabled: bool
    excluded_paths: List[str]


class UserConfig(BaseModel):
    server: ServerConfig
    enable_album_name_strip: bool
    enable_checkpoint_resume: bool
    filters: Optional[FilterConfig] = None
    conversions: List[Conversion]
    classification: ClassificationConfig
    duplicate_processing: Optional[DuplicateProcessingConfig] = None
    album_detection_from_folders: AlbumDetectionFromFoldersConfig

    create_album_from_date_if_missing: bool = False
