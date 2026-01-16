from enum import Enum, auto


class ModificationKind(Enum):
    ADD_TAG_TO_ASSET = auto()  # Tag added to asset
    REMOVE_TAG_FROM_ASSET = auto()  # Tag removed from asset
    REMOVE_TAG_GLOBALLY = auto()  # Tag deleted globally
    WARNING_TAG_REMOVAL_FROM_ASSET_FAILED = auto()  # Tag removal from asset failed
    WARNING_ASSET_ALREADY_IN_ALBUM = (
        auto()
    )  # Asset already in album (duplicate warning)
    CREATE_ALBUM = auto()  # Album created
    DELETE_ALBUM = auto()  # Album deleted
    RENAME_ALBUM = auto()  # Album renamed
    ASSIGN_ASSET_TO_ALBUM = auto()  # Asset assigned to album
    REMOVE_ASSET_FROM_ALBUM = auto()  # Asset removed from album
    UPDATE_ASSET_DATE = auto()  # Asset date updated

    # Asset is in an album whose date (from album name) differs from asset date by more than threshold
    ALBUM_DATE_MISMATCH = auto()  # Asset/album date mismatch detected

    # Classification conflicts
    CLASSIFICATION_CONFLICT = (
        auto()
    )  # Asset matched multiple classification rules (conflict detected)
    ALBUM_DETECTION_CONFLICT = (
        auto()
    )  # Multiple candidate folders found for album detection

    # Error tracking (recoverable errors during processing)
    ERROR_ASSET_SKIPPED_RECOVERABLE = (
        auto()
    )  # Asset skipped due to recoverable error (album deleted, etc.)
    ERROR_ALBUM_NOT_FOUND = auto()  # Album not found or deleted during processing
    ERROR_PERMISSION_DENIED = auto()  # Permission denied accessing resource
    ERROR_ASSET_DELETED = auto()  # Asset deleted during processing
    ERROR_NETWORK_TEMPORARY = auto()  # Temporary network error

    # Album permission assignment (Phase 1: detection/logging)
    ALBUM_PERMISSION_RULE_MATCHED = (
        auto()
    )  # Album matched permission rule (keyword match detected)
    ALBUM_PERMISSION_GROUPS_RESOLVED = auto()  # Groups and members resolved for album
    ALBUM_PERMISSION_NO_MATCH = auto()  # Album did not match any permission rule

    # Album permission execution (Phase 2: actual sharing)
    ALBUM_PERMISSION_SHARED = auto()  # Album successfully shared with users
    ALBUM_PERMISSION_REMOVED = auto()  # User removed from album (sync/unshare)
    ALBUM_PERMISSION_SHARE_FAILED = auto()  # Album sharing failed
