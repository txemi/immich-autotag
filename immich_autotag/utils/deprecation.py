"""
Utility to mark deprecated or unreachable code paths.
"""


class InternalDeprecationError(Exception):
    """
    Exception to indicate that a deprecated or invalid code path has been executed.
    """

    pass


def raise_deprecated_path(description: str) -> None:
    """
    Raises an InternalDeprecationError with an informative description.
    Usage: call at points in the code that should not be executed.
    """
    raise InternalDeprecationError(f"DEPRECATED PATH: {description}")
