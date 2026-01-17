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


class AlbumDateConsistencyConfig(BaseModel):
    """Configuration for album date consistency checks.

    This check compares the asset's taken date with its album's date
    and tags mismatches for user review.
    """

    enabled: bool = True
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    threshold_days: int = 180


class DuplicateProcessingConfig(BaseModel):
    autotag_album_conflict: Optional[str] = None
    autotag_classification_conflict: Optional[str] = None
    autotag_classification_conflict_prefix: Optional[str] = None
    autotag_album_detection_conflict: Optional[str] = None
    date_correction: DateCorrectionConfig


# Grouping of coupled fields in subclasses
class AlbumDetectionFromFoldersConfig(BaseModel):
    enabled: bool
    excluded_paths: List[str]


class PerformanceConfig(BaseModel):
    """Performance and debugging settings."""

    enable_type_checking: bool = Field(
        default=False,
        description="Enable @typechecked runtime type validation. Disable in production for ~50% performance improvement.",
    )


class UserGroup(BaseModel):
    """Represents a logical group of users for album sharing."""

    name: str = Field(..., description="Group name (e.g., 'familia', 'amigos')")
    description: Optional[str] = Field(
        None, description="Human-readable description of the group"
    )
    members: List[str] = Field(
        ...,
        description="List of member emails or user IDs",
        min_items=1,
    )


class AlbumSelectionRule(BaseModel):
    """Rule for selecting albums by keyword and assigning to groups."""

    name: str = Field(..., description="Rule name (e.g., 'Share with Familia')")
    keyword: str = Field(
        ...,
        description="Keyword to match in album name (case-insensitive word matching)",
    )
    groups: List[str] = Field(
        ..., description="List of group names to assign to matching albums", min_items=1
    )
    access: str = Field(
        default="view",
        description="Permission level: 'view', 'edit', or 'admin'",
        pattern="^(view|edit|admin)$",
    )


class AlbumPermissionsConfig(BaseModel):
    """Configuration for automatic album permission assignment."""

    enabled: bool = Field(default=False, description="Enable album permission feature")
    user_groups: Optional[List[UserGroup]] = Field(
        None, description="Define logical user groups"
    )
    selection_rules: Optional[List[AlbumSelectionRule]] = Field(
        None, description="Rules for matching albums to groups"
    )
    log_unmatched: bool = Field(
        default=False,
        description="Log albums that don't match any rule (can be noisy)",
    )


class PerformanceConfig(BaseModel):
    """Performance and debugging settings."""

    enable_type_checking: bool = Field(
        default=False,
        description="Enable @typechecked runtime type validation. Disable in production for ~50% performance improvement.",
    )

# --- Skip/Resume configuration ---
class SkipConfig(BaseModel):
    skip_n: int = Field(default=0, description="Número de elementos a saltar al procesar.")
    resume_previous: bool = Field(default=True, description="Si se debe continuar desde la ejecución anterior.")
    # antiguo     enable_checkpoint_resume: bool


class UserConfig(BaseModel):

    server: ServerConfig
    enable_album_name_strip: bool
    skip: Optional[SkipConfig] = Field(
        default=None,
        description="Configuración para saltar elementos y reanudar ejecuciones previas."
    )    

    filters: Optional[FilterConfig] = None
    conversions: List[Conversion]
    classification: ClassificationConfig
    duplicate_processing: Optional[DuplicateProcessingConfig] = None
    album_date_consistency: Optional[AlbumDateConsistencyConfig] = None
    album_detection_from_folders: AlbumDetectionFromFoldersConfig
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    album_permissions: Optional[AlbumPermissionsConfig] = Field(
        None, description="Configuration for automatic album permission assignment"
    )

    create_album_from_date_if_missing: bool = False
