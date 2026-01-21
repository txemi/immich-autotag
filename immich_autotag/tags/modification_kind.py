from dataclasses import dataclass
from enum import Enum

from immich_autotag.logging.levels import LogLevel


@dataclass(frozen=True)
class ModificationKindInfo:
    name: str
    log_level: LogLevel = LogLevel.FOCUS


class ModificationKind(Enum):
    ADD_TAG_TO_ASSET = ModificationKindInfo("ADD_TAG_TO_ASSET")
    REMOVE_TAG_FROM_ASSET = ModificationKindInfo("REMOVE_TAG_FROM_ASSET")
    REMOVE_TAG_GLOBALLY = ModificationKindInfo("REMOVE_TAG_GLOBALLY")
    WARNING_TAG_REMOVAL_FROM_ASSET_FAILED = ModificationKindInfo(
        "WARNING_TAG_REMOVAL_FROM_ASSET_FAILED"
    )
    WARNING_ASSET_ALREADY_IN_ALBUM = ModificationKindInfo(
        "WARNING_ASSET_ALREADY_IN_ALBUM"
    )
    CREATE_ALBUM = ModificationKindInfo("CREATE_ALBUM", LogLevel.PROGRESS)
    DELETE_ALBUM = ModificationKindInfo("DELETE_ALBUM", LogLevel.PROGRESS)
    RENAME_ALBUM = ModificationKindInfo("RENAME_ALBUM", LogLevel.PROGRESS)
    ASSIGN_ASSET_TO_ALBUM = ModificationKindInfo("ASSIGN_ASSET_TO_ALBUM")
    REMOVE_ASSET_FROM_ALBUM = ModificationKindInfo("REMOVE_ASSET_FROM_ALBUM")
    UPDATE_ASSET_DATE = ModificationKindInfo("UPDATE_ASSET_DATE")
    ALBUM_DATE_MISMATCH = ModificationKindInfo("ALBUM_DATE_MISMATCH")
    CLASSIFICATION_CONFLICT = ModificationKindInfo("CLASSIFICATION_CONFLICT")
    ALBUM_DETECTION_CONFLICT = ModificationKindInfo("ALBUM_DETECTION_CONFLICT")
    ERROR_ASSET_SKIPPED_RECOVERABLE = ModificationKindInfo(
        "ERROR_ASSET_SKIPPED_RECOVERABLE"
    )
    ERROR_ALBUM_NOT_FOUND = ModificationKindInfo("ERROR_ALBUM_NOT_FOUND")
    ERROR_PERMISSION_DENIED = ModificationKindInfo("ERROR_PERMISSION_DENIED")
    ERROR_ASSET_DELETED = ModificationKindInfo("ERROR_ASSET_DELETED")
    ERROR_NETWORK_TEMPORARY = ModificationKindInfo("ERROR_NETWORK_TEMPORARY")
    ALBUM_PERMISSION_RULE_MATCHED = ModificationKindInfo(
        "ALBUM_PERMISSION_RULE_MATCHED"
    )
    ALBUM_PERMISSION_GROUPS_RESOLVED = ModificationKindInfo(
        "ALBUM_PERMISSION_GROUPS_RESOLVED"
    )
    ALBUM_PERMISSION_NO_MATCH = ModificationKindInfo("ALBUM_PERMISSION_NO_MATCH")
    ALBUM_PERMISSION_SHARED = ModificationKindInfo("ALBUM_PERMISSION_SHARED")
    ALBUM_PERMISSION_REMOVED = ModificationKindInfo("ALBUM_PERMISSION_REMOVED")
    ALBUM_PERMISSION_SHARE_FAILED = ModificationKindInfo(
        "ALBUM_PERMISSION_SHARE_FAILED"
    )
    ADD_USER_TO_ALBUM = ModificationKindInfo("ADD_USER_TO_ALBUM", LogLevel.PROGRESS)
