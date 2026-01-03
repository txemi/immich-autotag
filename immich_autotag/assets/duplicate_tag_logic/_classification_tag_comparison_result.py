from enum import Enum, auto

class _ClassificationTagComparisonResult(Enum):
    EQUAL = "equal"
    AUTOFIX_OTHER = "autofix_other"
    AUTOFIX_SELF = "autofix_self"
    CONFLICT = "conflict"
