import enum


from enum import Enum
from immich_autotag.logging.levels import LogLevel

class ModificationKind(Enum):
    def __new__(cls, *args, log_level=None):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        obj._log_level = log_level or LogLevel.FOCUS
        return obj

    @property
    def log_level(self):
        return self._log_level

    ADD_TAG_TO_ASSET = ((),)
    REMOVE_TAG_FROM_ASSET = ((),)
    REMOVE_TAG_GLOBALLY = ((),)
    WARNING_TAG_REMOVAL_FROM_ASSET_FAILED = ((),)
    WARNING_ASSET_ALREADY_IN_ALBUM = ((),)
    CREATE_ALBUM = ((), {'log_level': LogLevel.PROGRESS})
    DELETE_ALBUM = ((), {'log_level': LogLevel.PROGRESS})
    RENAME_ALBUM = ((), {'log_level': LogLevel.PROGRESS})
    ASSIGN_ASSET_TO_ALBUM = ((),)
    REMOVE_ASSET_FROM_ALBUM = ((),)
    UPDATE_ASSET_DATE = ((),)
    ALBUM_DATE_MISMATCH = ((),)
    CLASSIFICATION_CONFLICT = ((),)
    ALBUM_DETECTION_CONFLICT = ((),)
    ERROR_ASSET_SKIPPED_RECOVERABLE = ((),)
    ERROR_ALBUM_NOT_FOUND = ((),)
    ERROR_PERMISSION_DENIED = ((),)
    ERROR_ASSET_DELETED = ((),)
    ERROR_NETWORK_TEMPORARY = ((),)
    ALBUM_PERMISSION_RULE_MATCHED = ((),)
    ALBUM_PERMISSION_GROUPS_RESOLVED = ((),)
    ALBUM_PERMISSION_NO_MATCH = ((),)
    ALBUM_PERMISSION_SHARED = ((),)
    ALBUM_PERMISSION_REMOVED = ((),)
    ALBUM_PERMISSION_SHARE_FAILED = ((),)

    ADD_USER_TO_ALBUM = ((), {'log_level': LogLevel.PROGRESS})