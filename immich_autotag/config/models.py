"""
models.py

Pydantic models for the new structured configuration (experimental).
"""

from typing import List, Optional
from enum import Enum

# Enum para modo de conversión
class ConversionMode(str, Enum):
    MOVE = "move"   # El valor destino sustituye al origen (el origen se elimina)
    COPY = "copy"   # El valor destino se añade, pero el origen se mantiene

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    model_config = {"extra": "forbid"}
    host: str
    port: int
    api_key: str


# Unified classification rule: can be by tag_names or album_name_patterns
from typing import Optional


class ClassificationRule(BaseModel):
    model_config = {"extra": "forbid"}
    tag_names: Optional[List[str]] = None
    album_name_patterns: Optional[List[str]] = None
    asset_links: Optional[List[str]] = None

    @classmethod
    def __get_pydantic_core_schema__(cls, *args, **kwargs):
        # Use the default schema, but add a custom validator
        from pydantic import GetCoreSchemaHandler
        from pydantic import core_schema
        schema = super().__get_pydantic_core_schema__(*args, **kwargs)
        def at_least_one_present(values):
            if (
                (not values.get('tag_names'))
                and (not values.get('album_name_patterns'))
                and (not values.get('asset_links'))
            ):
                raise ValueError(
                    'At least one of tag_names, album_name_patterns, or asset_links must be specified and non-empty.'
                )
            return values
        return core_schema.with_validator(schema, at_least_one_present)


class FilterConfig(BaseModel):
    model_config = {"extra": "forbid"}
    filter_in: List[ClassificationRule] = Field(default_factory=list)
    filter_out: List[ClassificationRule] = Field(default_factory=list)


class Destination(BaseModel):
    model_config = {"extra": "forbid"}
    album_names: Optional[List[str]] = None
    tag_names: Optional[List[str]] = None

class Conversion(BaseModel):
    model_config = {"extra": "forbid"}
    source: ClassificationRule
    destination: Destination
    mode: Optional[ConversionMode] = ConversionMode.MOVE


class ClassificationConfig(BaseModel):
    model_config = {"extra": "forbid"}
    rules: List[ClassificationRule] = Field(default_factory=list)
    autotag_unknown: Optional[str] = None
    autotag_conflict: Optional[str] = None


class DateCorrectionConfig(BaseModel):
    model_config = {"extra": "forbid"}
    enabled: bool
    extraction_timezone: str


class AlbumDateConsistencyConfig(BaseModel):
    """Configuration for album date consistency checks.

    This check compares the asset's taken date with its album's date
    and tags mismatches for user review.
    """

    model_config = {"extra": "forbid"}
    enabled: bool = True
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    threshold_days: int = 180


class DuplicateProcessingConfig(BaseModel):
    model_config = {"extra": "forbid"}
    autotag_album_conflict: Optional[str] = None
    autotag_classification_conflict: Optional[str] = None
    autotag_classification_conflict_prefix: Optional[str] = None
    autotag_album_detection_conflict: Optional[str] = None
    date_correction: DateCorrectionConfig


# Grouping of coupled fields in subclasses
class AlbumDetectionFromFoldersConfig(BaseModel):
    model_config = {"extra": "forbid"}
    enabled: bool
    excluded_paths: List[str]


class PerformanceConfig(BaseModel):
    """Performance and debugging settings."""
    model_config = {"extra": "forbid"}
    enable_type_checking: bool = Field(
        default=False,
        description="Enable @typechecked runtime type validation. Disable in production for ~50% performance improvement.",
    )


class UserGroup(BaseModel):
    """Represents a logical group of users for album sharing."""
    model_config = {"extra": "forbid"}
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
    model_config = {"extra": "forbid"}
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
    model_config = {"extra": "forbid"}
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
    model_config = {"extra": "forbid"}
    skip_n: int = Field(default=0, description="Número de elementos a saltar al procesar.")
    resume_previous: bool = Field(default=True, description="Si se debe continuar desde la ejecución anterior.")
    # antiguo     enable_checkpoint_resume: bool


class UserConfig(BaseModel):

    model_config = {"extra": "forbid"}
    server: ServerConfig
    enable_album_name_strip: bool
    skip: SkipConfig = Field(
        ...,
        description="Configuration for skipping items and resuming previous executions."
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
