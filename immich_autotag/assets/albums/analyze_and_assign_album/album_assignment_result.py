"""AlbumAssignmentResult enum for album assignment outcomes."""

from enum import Enum, auto


class AlbumAssignmentResult(Enum):
    """Enumeration of possible outcomes from album assignment logic."""

    CLASSIFIED = auto()
    CONFLICT = auto()
    ASSIGNED_UNIQUE = auto()
    CREATED_TEMPORARY = auto()
    UNCLASSIFIED_NO_ALBUM = auto()
    ERROR = auto()
