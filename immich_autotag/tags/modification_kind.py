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
