from enum import Enum


class ClassificationTagComparisonResult(Enum):
    EQUAL = "equal"
    AUTOFIX_OTHER = "autofix_other"
    AUTOFIX_SELF = "autofix_self"
    CONFLICT = "conflict"
