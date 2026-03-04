from enum import Enum

import attrs

from immich_autotag.logging.levels import LogLevel


class ModificationLevel(Enum):
    """Defines the severity/type of a modification entry."""

    ERROR = "error"  # Critical errors that prevented action
    WARNING = "warning"  # Non-critical issues that were handled gracefully
    MODIFICATION = "modification"  # Successful action/change
    UNKNOWN = "unknown"  # Unknown or unclassifiable level (should be avoided)
    READ_ONLY = "read_only"  # Informational entries that did not involve a change

    def is_error(self) -> bool:
        return self == ModificationLevel.ERROR

    def is_warning(self) -> bool:
        return self == ModificationLevel.WARNING

    def is_modification(self) -> bool:
        return self == ModificationLevel.MODIFICATION

    def is_unknown(self) -> bool:
        return self == ModificationLevel.UNKNOWN


@attrs.define(frozen=True, auto_attribs=True, slots=True, kw_only=True)
class ModificationKindInfo:
    _name: str = attrs.field(alias="name")
    _log_level: LogLevel | None = attrs.field(
        alias="log_level", init=False, default=None
    )
    _level: ModificationLevel = attrs.field(alias="level")
    _requires_asset: bool = attrs.field(alias="requires_asset")
    _requires_album: bool = attrs.field(alias="requires_album")
    _requires_tag: bool = attrs.field(alias="requires_tag")

    def get_name(self) -> str:
        return self._name

    def get_log_level(self) -> LogLevel:
        if self._log_level is not None:
            return self._log_level
        # Dynamic fallback based on modification level
        match self._level:
            case ModificationLevel.MODIFICATION:
                return LogLevel.PROGRESS
            case ModificationLevel.WARNING:
                return LogLevel.WARNING
            case ModificationLevel.ERROR:
                return LogLevel.ERROR
            case ModificationLevel.UNKNOWN:
                return LogLevel.IMPORTANT
        # Fallback (should not happen)
        return LogLevel.IMPORTANT

    def get_level(self) -> ModificationLevel:
        return self._level

    def requires_asset(self) -> bool:
        return self._requires_asset

    def requires_album(self) -> bool:
        return self._requires_album

    def requires_tag(self) -> bool:
        return self._requires_tag

    def is_change(self) -> bool:
        """Return True if this kind represents a modification/change."""
        return self._level.is_modification()


class ModificationKind(Enum):

    # --- Asset-related modifications ---
    ADD_TAG_TO_ASSET = ModificationKindInfo(
        name="ADD_TAG_TO_ASSET",
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    REMOVE_TAG_FROM_ASSET = ModificationKindInfo(
        name="REMOVE_TAG_FROM_ASSET",
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    REMOVE_TAG_GLOBALLY = ModificationKindInfo(
        name="REMOVE_TAG_GLOBALLY",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=False,
        requires_tag=True,
    )
    CREATE_TAG = ModificationKindInfo(
        name="CREATE_TAG",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=False,
        requires_tag=True,
    )
    WARNING_TAG_REMOVAL_FROM_ASSET_FAILED = ModificationKindInfo(
        name="WARNING_TAG_REMOVAL_FROM_ASSET_FAILED",
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    WARNING_TAG_ADDITION_TO_ASSET_FAILED = ModificationKindInfo(
        name="WARNING_TAG_ADDITION_TO_ASSET_FAILED",
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    WARNING_ASSET_ALREADY_IN_ALBUM = ModificationKindInfo(
        name="WARNING_ASSET_ALREADY_IN_ALBUM",
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    WARNING_ASSET_NOT_IN_ALBUM = ModificationKindInfo(
        name="WARNING_ASSET_NOT_IN_ALBUM",
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    ASSIGN_ASSET_TO_ALBUM = ModificationKindInfo(
        name="ASSIGN_ASSET_TO_ALBUM",
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    REMOVE_ASSET_FROM_ALBUM = ModificationKindInfo(
        name="REMOVE_ASSET_FROM_ALBUM",
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    UPDATE_ASSET_DATE = ModificationKindInfo(
        name="UPDATE_ASSET_DATE",
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_ASSET_SKIPPED_RECOVERABLE = ModificationKindInfo(
        name="ERROR_ASSET_SKIPPED_RECOVERABLE",
        level=ModificationLevel.ERROR,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_ASSET_SKIPPED_FATAL = ModificationKindInfo(
        name="ERROR_ASSET_SKIPPED_FATAL",
        level=ModificationLevel.ERROR,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_ASSET_DELETED = ModificationKindInfo(
        name="ERROR_ASSET_DELETED",
        level=ModificationLevel.ERROR,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )

    # --- Album-related modifications ---
    CREATE_ALBUM = ModificationKindInfo(
        name="CREATE_ALBUM",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    DELETE_ALBUM = ModificationKindInfo(
        name="DELETE_ALBUM",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    DELETE_ALBUM_UNHEALTHY = ModificationKindInfo(
        name="DELETE_ALBUM_UNHEALTHY",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    RENAME_ALBUM = ModificationKindInfo(
        name="RENAME_ALBUM",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_DATE_MISMATCH = ModificationKindInfo(
        name="ALBUM_DATE_MISMATCH",
        level=ModificationLevel.WARNING,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_DETECTION_CONFLICT = ModificationKindInfo(
        name="ALBUM_DETECTION_CONFLICT",
        level=ModificationLevel.WARNING,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )
    CLASSIFICATION_CONFLICT = ModificationKindInfo(
        name="CLASSIFICATION_CONFLICT",
        level=ModificationLevel.WARNING,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )

    # --- Authorization/permission-related modifications ---
    ALBUM_PERMISSION_RULE_MATCHED = ModificationKindInfo(
        name="ALBUM_PERMISSION_RULE_MATCHED",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_GROUPS_RESOLVED = ModificationKindInfo(
        name="ALBUM_PERMISSION_GROUPS_RESOLVED",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_NO_MATCH = ModificationKindInfo(
        name="ALBUM_PERMISSION_NO_MATCH",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_SHARED = ModificationKindInfo(
        name="ALBUM_PERMISSION_SHARED",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_REMOVED = ModificationKindInfo(
        name="ALBUM_PERMISSION_REMOVED",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_SHARE_FAILED = ModificationKindInfo(
        name="ALBUM_PERMISSION_SHARE_FAILED",
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ADD_USER_TO_ALBUM = ModificationKindInfo(
        name="ADD_USER_TO_ALBUM",
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )

    # --- Error-related modifications ---
    ERROR_ALBUM_NOT_FOUND = ModificationKindInfo(
        name="ERROR_ALBUM_NOT_FOUND",
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ERROR_PERMISSION_DENIED = ModificationKindInfo(
        name="ERROR_PERMISSION_DENIED",
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_NETWORK_TEMPORARY = ModificationKindInfo(
        name="ERROR_NETWORK_TEMPORARY",
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )

    def get_level(self) -> ModificationLevel:
        return self.value.get_level()

    def is_error(self) -> bool:
        return self.get_level().is_error()

    def is_warning(self) -> bool:
        return self.get_level().is_warning()

    def is_modification(self) -> bool:
        return self.get_level().is_modification()

    def is_unknown(self) -> bool:
        return self.get_level().is_unknown()

    def is_change(self) -> bool:
        """Return True if this kind represents a modification/change."""
        return self.value.is_change()
