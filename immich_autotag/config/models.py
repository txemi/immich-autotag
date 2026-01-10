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


class Conversion(BaseModel):
    source: ClassificationRule
    destination: ClassificationRule


class AutoTagsConfig(BaseModel):
    enabled: bool
    category_unknown: str
    category_conflict: str
    duplicate_asset_album_conflict: str
    duplicate_asset_classification_conflict: str
    duplicate_asset_classification_conflict_prefix: str
    album_date_mismatch: str = Field(
        default="autotag_output_album_date_mismatch",
        description="Tag for album/asset date mismatch. Used if not specified by user."
    )


# todo: not sure what this is, was it in the original config file?
class AdvancedFeatureConfig(BaseModel):
    enabled: bool
    threshold: float


# Grouping of coupled fields in subclasses
class AlbumDetectionFromFoldersConfig(BaseModel):
    enabled: bool
    excluded_paths: List[str]


class DateCorrectionConfig(BaseModel):
    enabled: bool
    extraction_timezone: str


class FeaturesConfig(BaseModel):
    enable_album_detection: bool
    enable_tag_suggestion: bool
    advanced_feature: Optional[AdvancedFeatureConfig]
    enable_album_name_strip: bool
    album_detection_from_folders: AlbumDetectionFromFoldersConfig
    date_correction: DateCorrectionConfig
    enable_checkpoint_resume: bool


class UserConfig(BaseModel):
    server: ServerConfig
    filter_out_asset_links: List[str]
    classification_rules: List[ClassificationRule]
    conversions: List[Conversion]
    auto_tags: AutoTagsConfig
    features: FeaturesConfig
