
from enum import Enum

import attrs

from immich_autotag.logging.levels import LogLevel


class ModificationLevel(Enum):
    """Defines the severity/type of a modification entry."""

    ERROR = "error"  # Critical errors that prevented action
    WARNING = "warning"  # Non-critical issues that were handled gracefully
    MODIFICATION = "modification"  # Successful action/change
    UNKNOWN = "unknown"  # Unknown or unclassifiable level (should be avoided)

    def is_error(self) -> bool:
        return self == ModificationLevel.ERROR

    def is_warning(self) -> bool:
        return self == ModificationLevel.WARNING

    def is_modification(self) -> bool:
        return self == ModificationLevel.MODIFICATION

    def is_unknown(self) -> bool:
        return self == ModificationLevel.UNKNOWN


@attrs.define(frozen=True, auto_attribs=True, slots=True)
class ModificationKindInfo:
    name: str = attrs.field(type=str)
    log_level: LogLevel = attrs.field(type=LogLevel)
    level: ModificationLevel = attrs.field(type=ModificationLevel)
    # is_error/is_change removed; use methods instead
    _requires_asset: bool = attrs.field(type=bool, alias="requires_asset")
    _requires_album: bool = attrs.field(type=bool, alias="requires_album")
    _requires_tag: bool = attrs.field(type=bool, alias="requires_tag")

    def requires_asset(self) -> bool:
        return self._requires_asset

    def requires_album(self) -> bool:
        return self._requires_album

    def requires_tag(self) -> bool:
        return self._requires_tag
    def is_change(self: "ModificationKind") -> bool:  # type: ignore
        # Consider a change if the level is MODIFICATION
        return self.value.level.is_modification()  # type: ignore[attr-defined]

class ModificationKind(Enum):

    # --- Asset-related modifications ---
    ADD_TAG_TO_ASSET = ModificationKindInfo(
        name="ADD_TAG_TO_ASSET",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    REMOVE_TAG_FROM_ASSET = ModificationKindInfo(
        name="REMOVE_TAG_FROM_ASSET",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    REMOVE_TAG_GLOBALLY = ModificationKindInfo(
        name="REMOVE_TAG_GLOBALLY",
        log_level=LogLevel.IMPORTANT,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=False,
        requires_tag=True,
    )
    CREATE_TAG = ModificationKindInfo(
        name="CREATE_TAG",
        log_level=LogLevel.IMPORTANT,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=False,
        requires_tag=True,
    )
    WARNING_TAG_REMOVAL_FROM_ASSET_FAILED = ModificationKindInfo(
        name="WARNING_TAG_REMOVAL_FROM_ASSET_FAILED",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    WARNING_TAG_ADDITION_TO_ASSET_FAILED = ModificationKindInfo(
        name="WARNING_TAG_ADDITION_TO_ASSET_FAILED",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=False,
        requires_tag=True,
    )
    WARNING_ASSET_ALREADY_IN_ALBUM = ModificationKindInfo(
        name="WARNING_ASSET_ALREADY_IN_ALBUM",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    WARNING_ASSET_NOT_IN_ALBUM = ModificationKindInfo(
        name="WARNING_ASSET_NOT_IN_ALBUM",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    ASSIGN_ASSET_TO_ALBUM = ModificationKindInfo(
        name="ASSIGN_ASSET_TO_ALBUM",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    REMOVE_ASSET_FROM_ALBUM = ModificationKindInfo(
        name="REMOVE_ASSET_FROM_ALBUM",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=True,
        requires_tag=False,
    )
    UPDATE_ASSET_DATE = ModificationKindInfo(
        name="UPDATE_ASSET_DATE",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_ASSET_SKIPPED_RECOVERABLE = ModificationKindInfo(
        name="ERROR_ASSET_SKIPPED_RECOVERABLE",
        log_level=LogLevel.ERROR,
        level=ModificationLevel.ERROR,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_ASSET_DELETED = ModificationKindInfo(
        name="ERROR_ASSET_DELETED",
        log_level=LogLevel.ERROR,
        level=ModificationLevel.ERROR,
        requires_asset=True,
        requires_album=False,
        requires_tag=False,
    )

    # --- Album-related modifications ---
    CREATE_ALBUM = ModificationKindInfo(
        name="CREATE_ALBUM",
        log_level=LogLevel.IMPORTANT,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    DELETE_ALBUM = ModificationKindInfo(
        name="DELETE_ALBUM",
        log_level=LogLevel.IMPORTANT,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    DELETE_ALBUM_UNHEALTHY = ModificationKindInfo(
        name="DELETE_ALBUM_UNHEALTHY",
        log_level=LogLevel.IMPORTANT,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    RENAME_ALBUM = ModificationKindInfo(
        name="RENAME_ALBUM",
        log_level=LogLevel.PROGRESS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_DATE_MISMATCH = ModificationKindInfo(
        name="ALBUM_DATE_MISMATCH",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_DETECTION_CONFLICT = ModificationKindInfo(
        name="ALBUM_DETECTION_CONFLICT",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    CLASSIFICATION_CONFLICT = ModificationKindInfo(
        name="CLASSIFICATION_CONFLICT",
        log_level=LogLevel.WARNING,
        level=ModificationLevel.WARNING,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )

    # --- Authorization/permission-related modifications ---
    ALBUM_PERMISSION_RULE_MATCHED = ModificationKindInfo(
        name="ALBUM_PERMISSION_RULE_MATCHED",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_GROUPS_RESOLVED = ModificationKindInfo(
        name="ALBUM_PERMISSION_GROUPS_RESOLVED",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_NO_MATCH = ModificationKindInfo(
        name="ALBUM_PERMISSION_NO_MATCH",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_SHARED = ModificationKindInfo(
        name="ALBUM_PERMISSION_SHARED",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_REMOVED = ModificationKindInfo(
        name="ALBUM_PERMISSION_REMOVED",
        log_level=LogLevel.FOCUS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ALBUM_PERMISSION_SHARE_FAILED = ModificationKindInfo(
        name="ALBUM_PERMISSION_SHARE_FAILED",
        log_level=LogLevel.ERROR,
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ADD_USER_TO_ALBUM = ModificationKindInfo(
        name="ADD_USER_TO_ALBUM",
        log_level=LogLevel.PROGRESS,
        level=ModificationLevel.MODIFICATION,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )

    # --- Error-related modifications ---
    ERROR_ALBUM_NOT_FOUND = ModificationKindInfo(
        name="ERROR_ALBUM_NOT_FOUND",
        log_level=LogLevel.ERROR,
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=True,
        requires_tag=False,
    )
    ERROR_PERMISSION_DENIED = ModificationKindInfo(
        name="ERROR_PERMISSION_DENIED",
        log_level=LogLevel.ERROR,
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )
    ERROR_NETWORK_TEMPORARY = ModificationKindInfo(
        name="ERROR_NETWORK_TEMPORARY",
        log_level=LogLevel.ERROR,
        level=ModificationLevel.ERROR,
        requires_asset=False,
        requires_album=False,
        requires_tag=False,
    )

    def get_level(self) -> ModificationLevel:
        return self.value.level

    def is_error(self) -> bool:
        return self.get_level().is_error()

    def is_warning(self) -> bool:
        return self.get_level().is_warning()

    def is_modification(self) -> bool:
        return self.get_level().is_modification()

    def is_unknown(self) -> bool:
        return self.get_level().is_unknown()
