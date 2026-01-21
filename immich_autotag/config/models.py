"""
models.py

Pydantic models for the new structured configuration (experimental).
"""

from enum import Enum
from typing import List, Optional


# Enum for conversion mode
# Enum for conversion mode
class ConversionMode(str, Enum):
    MOVE = "move"  # MOVE: When the conversion is applied, the destination values replace the source values. That is, the source tags and albums are removed and the destination ones are assigned. (Classic "convert" or "move" behavior)
    COPY = "copy"  # COPY: When the conversion is applied, the destination values are added, but the source values are kept. That is, the destination tags and albums are added without removing the source ones. ("Copy"-type behavior)


from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """
    Configuration for connecting to the Immich server API.
    Includes connection details and authentication key.
    """

    model_config = {"extra": "forbid"}
    host: str = Field(
        ..., description="Immich server host (e.g., 'localhost' or IP address)"
    )
    port: int = Field(..., description="Immich server port (e.g., 2283)")
    api_key: str = Field(
        ..., description="API key for authenticating with the Immich server"
    )


# Unified classification rule: can be by tag_names or album_name_patterns


class ClassificationRule(BaseModel):
    model_config = {"extra": "forbid"}
    tag_names: Optional[List[str]] = None
    album_name_patterns: Optional[List[str]] = None
    asset_links: Optional[List[str]] = None

    @classmethod
    def model_validate(cls, value):
        # Use the default validation, then check at least one field is present
        obj = super().model_validate(value)
        if not (obj.tag_names or obj.album_name_patterns or obj.asset_links):
            raise ValueError(
                "At least one of tag_names, album_name_patterns, or asset_links must be specified and non-empty."
            )
        return obj


class FilterConfig(BaseModel):
    """
    Filter to limit the set of items to process.
    - filter_in: positive filter; only items matching any of the rules will be processed.
    - filter_out: negative filter; items matching any of the rules will be excluded from processing.
    If both are empty, all items are processed.
    """

    model_config = {"extra": "forbid"}
    filter_in: List[ClassificationRule] = Field(
        default_factory=list,
        description="Positive filter: only items matching these rules will be processed.",
    )
    filter_out: List[ClassificationRule] = Field(
        default_factory=list,
        description="Negative filter: items matching these rules will be excluded from processing.",
    )


class Destination(BaseModel):
    """
    Represents actions to perform on assets (photos or videos).
    Allows specifying which albums and tags to associate with assets affected by a conversion.
    """

    model_config = {"extra": "forbid"}
    album_names: Optional[List[str]] = Field(
        default=None, description="Album names to assign to the affected assets."
    )
    tag_names: Optional[List[str]] = Field(
        default=None, description="Tag names to assign to the affected assets."
    )


class Conversion(BaseModel):
    """
    Defines rules to automatically apply tags or albums to items (photos or videos) that meet certain conditions.
    Used in autotag processing to transform asset classification according to declarative rules.
    """

    model_config = {"extra": "forbid"}
    source: ClassificationRule = Field(
        ..., description="Rule to match source assets for conversion."
    )
    destination: Destination = Field(
        ..., description="Destination albums and tags to assign."
    )
    mode: Optional[ConversionMode] = Field(
        default=ConversionMode.MOVE,
        description="Conversion mode: 'move' replaces source values, 'copy' adds destination values.",
    )
    description: Optional[str] = Field(
        default=None, description="Optional description for the conversion rule."
    )


class ClassificationConfig(BaseModel):
    """
    Allows the user to define classification categories to use in the application.
    Each rule defines a category (by tags, album patterns, etc). The system will automatically tag:
    - Items that do not belong to any category (using autotag_unknown)
    - Items that belong to more than one category (using autotag_conflict)
    This helps the user easily detect unclassified or conflicting assets and resolve them manually.
    """

    model_config = {"extra": "forbid"}
    rules: List[ClassificationRule] = Field(
        default_factory=list, description="List of classification rules."
    )
    autotag_unknown: Optional[str] = Field(
        default="autotag_output_unknown",
        description="Tag to assign to assets not matching any category.",
    )
    autotag_conflict: Optional[str] = Field(
        default="autotag_output_conflict",
        description="Tag to assign to assets matching multiple categories.",
    )


class DateCorrectionConfig(BaseModel):
    """
    Configuration for correcting asset dates.
    If enabled, the system will try to obtain a more accurate date than the one in Immich by:
    - Using the date from duplicates (if available and more reliable)
    - Extracting the date from the filename if it matches known patterns (e.g., WhatsApp or Android photos)
    - Using the specified timezone to adjust the extracted date
    """

    model_config = {"extra": "forbid"}
    enabled: bool = Field(..., description="Enable date correction for assets.")
    extraction_timezone: str = Field(
        ..., description="Timezone to use for adjusting extracted dates."
    )


class AlbumDateConsistencyConfig(BaseModel):
    """
    Configuration for album date consistency checks.
    Compares the asset's taken date with its album's date and tags mismatches for user review.
    """

    model_config = {"extra": "forbid"}
    enabled: bool = Field(
        default=True, description="Enable album date consistency checks."
    )
    autotag_album_date_mismatch: str = Field(
        default="autotag_output_album_date_mismatch",
        description="Tag to assign to assets with album date mismatches.",
    )
    threshold_days: int = Field(
        default=180, description="Threshold in days for considering a date mismatch."
    )


class DuplicateProcessingConfig(BaseModel):
    """
    Configuration for duplicate asset processing.
    Uses duplicates detected by Immich to identify discrepancies between duplicate items.
    This allows detection and tagging of differences in date, classification, or albums, since all duplicates should ideally match in these aspects.
    """

    model_config = {"extra": "forbid"}
    autotag_album_conflict: Optional[str] = Field(
        default="autotag_output_duplicate_asset_album_conflict",
        description="Tag for assets with album conflicts among duplicates.",
    )
    autotag_classification_conflict: Optional[str] = Field(
        default="autotag_output_duplicate_asset_classification_conflict",
        description="Tag for assets with classification conflicts among duplicates.",
    )
    autotag_classification_conflict_prefix: Optional[str] = Field(
        default="autotag_output_duplicate_asset_classification_conflict_",
        description="Prefix for tags indicating classification conflicts.",
    )
    autotag_album_detection_conflict: Optional[str] = Field(
        default="autotag_output_album_detection_conflict",
        description="Tag for assets with album detection conflicts among duplicates.",
    )
    date_correction: DateCorrectionConfig = Field(
        ..., description="Date correction configuration for duplicates."
    )


# Grouping of coupled fields in subclasses
class AlbumDetectionFromFoldersConfig(BaseModel):
    """
    Configuration for automatic album creation from folders containing a date in their name.

    If enabled, the system will scan folder paths (not just the immediate parent) for date patterns.
    For each folder that includes a date, a daily album will be created for the assets within.
    Folders listed in 'excluded_paths' will be ignored.
    """

    model_config = {"extra": "forbid"}
    enabled: bool = Field(
        ...,
        description="Enable automatic album creation from folders with a date in their name.",
    )
    excluded_paths: List[str] = Field(
        ..., description="List of folder paths to exclude from album detection."
    )


class PerformanceConfig(BaseModel):
    """
    Performance and debugging settings.
    """

    model_config = {"extra": "forbid"}
    enable_type_checking: bool = Field(
        default=False,
        description="Enable @typechecked runtime type validation. Disable in production for ~50% performance improvement.",
    )


class UserGroup(BaseModel):
    """
    Represents a logical group of users for album sharing.
    """

    model_config = {"extra": "forbid"}
    name: str = Field(..., description="Group name (e.g., 'family', 'friends').")
    description: Optional[str] = Field(
        None, description="Human-readable description of the group."
    )
    members: List[str] = Field(..., description="List of member emails or user IDs.")


class AlbumSelectionRule(BaseModel):
    """
    Rule for selecting albums by keyword and assigning to groups.
    """

    model_config = {"extra": "forbid"}
    name: str = Field(..., description="Rule name (e.g., 'Share with Family').")
    keyword: str = Field(
        ...,
        description="Keyword to match in album name (case-insensitive word matching).",
    )
    groups: List[str] = Field(
        ...,
        description="List of group names to assign to matching albums.",
    )
    access: str = Field(
        default="view",
        description="Permission level: 'view', 'edit', or 'admin'.",
        pattern="^(view|edit|admin)$",
    )


class AlbumPermissionsConfig(BaseModel):
    """
    Configuration for automatic album permission assignment.
    """

    model_config = {"extra": "forbid"}
    enabled: bool = Field(default=False, description="Enable album permission feature.")
    user_groups: Optional[List[UserGroup]] = Field(
        None, description="Define logical user groups."
    )
    selection_rules: Optional[List[AlbumSelectionRule]] = Field(
        None, description="Rules for matching albums to groups."
    )
    log_unmatched: bool = Field(
        default=False,
        description="Log albums that don't match any rule (can be noisy).",
    )


# --- Skip/Resume configuration ---
class SkipConfig(BaseModel):
    """
    Configuration for skipping and limiting the processing of items.
    Allows specifying how many initial items to skip (skip_n).
    If resume_previous is True, skip_n can be set automatically from the previous run (e.g., to resume after a failure).
    The max_items field limits the maximum number of items to process in the current run.
    """

    model_config = {"extra": "forbid"}
    skip_n: int = Field(
        default=0, description="Number of items to skip when processing."
    )
    resume_previous: bool = Field(
        default=True, description="Whether to continue from the previous execution."
    )
    max_items: Optional[int] = Field(
        default=None,
        description="Maximum number of items to process in this run. If None, no limit.",
    )
    # formerly: enable_checkpoint_resume


class UserConfig(BaseModel):
    """
    Main configuration object for the Immich autotag system.
    Can be constructed directly in Python or deserialized/serialized from and to a text file (YAML or Python).
    Includes all parameters and configuration blocks required for system operation.
    """

    model_config = {"extra": "forbid"}
    server: ServerConfig = Field(
        ..., description="Immich server connection configuration."
    )
    enable_album_name_strip: bool = Field(
        ..., description="Enable stripping of album names."
    )
    skip: SkipConfig = Field(
        ...,
        description="Configuration for skipping items and resuming previous executions.",
    )
    filters: Optional[FilterConfig] = Field(
        default=None, description="Filter configuration for item selection."
    )
    conversions: List[Conversion] = Field(
        ..., description="List of conversion rules to apply."
    )
    classification: ClassificationConfig = Field(
        ..., description="Classification configuration block."
    )
    duplicate_processing: Optional[DuplicateProcessingConfig] = Field(
        default=None, description="Duplicate processing configuration block."
    )
    album_date_consistency: Optional[AlbumDateConsistencyConfig] = Field(
        default=None, description="Album date consistency check configuration."
    )
    album_detection_from_folders: AlbumDetectionFromFoldersConfig = Field(
        ..., description="Configuration for album detection from folders."
    )
    performance: PerformanceConfig = Field(
        default_factory=PerformanceConfig,
        description="Performance and debugging settings.",
    )
    album_permissions: Optional[AlbumPermissionsConfig] = Field(
        default=None,
        description="Configuration for automatic album permission assignment.",
    )
    create_album_from_date_if_missing: bool = Field(
        default=False, description="Create album from date if missing."
    )
