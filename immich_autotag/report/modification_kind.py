from dataclasses import dataclass
from enum import Enum

from immich_autotag.logging.levels import LogLevel


class ModificationLevel(Enum):
    """Defines the severity/type of a modification entry."""

    ERROR = "error"  # Critical errors that prevented action
    WARNING = "warning"  # Non-critical issues that were handled gracefully
    MODIFICATION = "modification"  # Successful action/change
    UNKNOWN = "unknown"  # Unknown or unclassifiable level (should be avoided)


@dataclass(frozen=True)
class ModificationKindInfo:
    name: str
    log_level: LogLevel = LogLevel.FOCUS
    level: ModificationLevel = (
        ModificationLevel.UNKNOWN
    )  # Default to UNKNOWN - must be explicit


class ModificationKind(Enum):

    # --- Asset-related modifications ---
    ADD_TAG_TO_ASSET = ModificationKindInfo(
        "ADD_TAG_TO_ASSET", level=ModificationLevel.MODIFICATION
    )
    REMOVE_TAG_FROM_ASSET = ModificationKindInfo(
        "REMOVE_TAG_FROM_ASSET", level=ModificationLevel.MODIFICATION
    )
    REMOVE_TAG_GLOBALLY = ModificationKindInfo(
        "REMOVE_TAG_GLOBALLY", LogLevel.IMPORTANT, ModificationLevel.MODIFICATION
    )
    WARNING_TAG_REMOVAL_FROM_ASSET_FAILED = ModificationKindInfo(
        "WARNING_TAG_REMOVAL_FROM_ASSET_FAILED",
        LogLevel.WARNING,
        ModificationLevel.WARNING,
    )
    WARNING_TAG_ADDITION_TO_ASSET_FAILED = ModificationKindInfo(
        "WARNING_TAG_ADDITION_TO_ASSET_FAILED",
        LogLevel.WARNING,
        ModificationLevel.WARNING,
    )
    WARNING_ASSET_ALREADY_IN_ALBUM = ModificationKindInfo(
        "WARNING_ASSET_ALREADY_IN_ALBUM", LogLevel.WARNING, ModificationLevel.WARNING
    )
    ASSIGN_ASSET_TO_ALBUM = ModificationKindInfo(
        "ASSIGN_ASSET_TO_ALBUM", level=ModificationLevel.MODIFICATION
    )
    REMOVE_ASSET_FROM_ALBUM = ModificationKindInfo(
        "REMOVE_ASSET_FROM_ALBUM", level=ModificationLevel.MODIFICATION
    )
    UPDATE_ASSET_DATE = ModificationKindInfo(
        "UPDATE_ASSET_DATE", level=ModificationLevel.MODIFICATION
    )
    ERROR_ASSET_SKIPPED_RECOVERABLE = ModificationKindInfo(
        "ERROR_ASSET_SKIPPED_RECOVERABLE", LogLevel.ERROR, ModificationLevel.ERROR
    )
    ERROR_ASSET_DELETED = ModificationKindInfo(
        "ERROR_ASSET_DELETED", LogLevel.ERROR, ModificationLevel.ERROR
    )

    # --- Album-related modifications ---
    CREATE_ALBUM = ModificationKindInfo(
        "CREATE_ALBUM", LogLevel.IMPORTANT, ModificationLevel.MODIFICATION
    )
    DELETE_ALBUM = ModificationKindInfo(
        "DELETE_ALBUM", LogLevel.IMPORTANT, ModificationLevel.MODIFICATION
    )
    DELETE_ALBUM_UNHEALTHY = ModificationKindInfo(
        "DELETE_ALBUM_UNHEALTHY", LogLevel.IMPORTANT, ModificationLevel.MODIFICATION
    )
    RENAME_ALBUM = ModificationKindInfo(
        "RENAME_ALBUM", LogLevel.PROGRESS, ModificationLevel.MODIFICATION
    )
    ALBUM_DATE_MISMATCH = ModificationKindInfo(
        "ALBUM_DATE_MISMATCH", LogLevel.WARNING, ModificationLevel.WARNING
    )
    ALBUM_DETECTION_CONFLICT = ModificationKindInfo(
        "ALBUM_DETECTION_CONFLICT", LogLevel.WARNING, ModificationLevel.WARNING
    )
    CLASSIFICATION_CONFLICT = ModificationKindInfo(
        "CLASSIFICATION_CONFLICT", LogLevel.WARNING, ModificationLevel.WARNING
    )

    # --- Authorization/permission-related modifications ---
    ALBUM_PERMISSION_RULE_MATCHED = ModificationKindInfo(
        "ALBUM_PERMISSION_RULE_MATCHED", level=ModificationLevel.MODIFICATION
    )
    ALBUM_PERMISSION_GROUPS_RESOLVED = ModificationKindInfo(
        "ALBUM_PERMISSION_GROUPS_RESOLVED", level=ModificationLevel.MODIFICATION
    )
    ALBUM_PERMISSION_NO_MATCH = ModificationKindInfo(
        "ALBUM_PERMISSION_NO_MATCH", level=ModificationLevel.MODIFICATION
    )
    ALBUM_PERMISSION_SHARED = ModificationKindInfo(
        "ALBUM_PERMISSION_SHARED", level=ModificationLevel.MODIFICATION
    )
    ALBUM_PERMISSION_REMOVED = ModificationKindInfo(
        "ALBUM_PERMISSION_REMOVED", level=ModificationLevel.MODIFICATION
    )
    ALBUM_PERMISSION_SHARE_FAILED = ModificationKindInfo(
        "ALBUM_PERMISSION_SHARE_FAILED", LogLevel.ERROR, ModificationLevel.ERROR
    )
    ADD_USER_TO_ALBUM = ModificationKindInfo(
        "ADD_USER_TO_ALBUM", LogLevel.PROGRESS, ModificationLevel.MODIFICATION
    )

    # --- Error-related modifications ---
    ERROR_ALBUM_NOT_FOUND = ModificationKindInfo(
        "ERROR_ALBUM_NOT_FOUND", LogLevel.ERROR, ModificationLevel.ERROR
    )
    ERROR_PERMISSION_DENIED = ModificationKindInfo(
        "ERROR_PERMISSION_DENIED", LogLevel.ERROR, ModificationLevel.ERROR
    )
    ERROR_NETWORK_TEMPORARY = ModificationKindInfo(
        "ERROR_NETWORK_TEMPORARY", LogLevel.ERROR, ModificationLevel.ERROR
    )

    def get_level(self) -> ModificationLevel:
        """Returns the level (ERROR, WARNING, MODIFICATION, or UNKNOWN) for this kind."""
        return self.value.level

    def is_error(self) -> bool:
        """Returns True if this kind represents an error."""
        return self.get_level() == ModificationLevel.ERROR

    def is_warning(self) -> bool:
        """Returns True if this kind represents a warning."""
        return self.get_level() == ModificationLevel.WARNING

    def is_modification(self) -> bool:
        """Returns True if this kind represents a successful modification."""
        return self.get_level() == ModificationLevel.MODIFICATION

    def is_unknown(self) -> bool:
        """Returns True if this kind's level is unknown or unclassified."""
        return self.get_level() == ModificationLevel.UNKNOWN
