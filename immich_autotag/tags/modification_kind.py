from enum import Enum, auto


class ModificationKind(Enum):
    ADD = auto()  # Tag added to asset
    REMOVE = auto()  # Tag removed from asset
    WARNING_REMOVAL_FAILED = auto()  # Tag removal failed
    CREATE_ALBUM = auto()  # Album created
    RENAME_ALBUM = auto()  # Album renamed
    ASSIGN_ASSET_TO_ALBUM = auto()  # Asset assigned to album
