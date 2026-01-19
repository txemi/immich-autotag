"""
Error classification system for distinguishing recoverable vs fatal errors during asset processing.

Recoverable errors: Can be skipped, log warning, continue to next asset
  - Album deleted/not found (400 from API)
  - Permission issues (403 from API)
  - Asset deleted during processing
  - Temporary network issues (configurable)

Fatal errors: Should fail immediately
  - Programming errors (AttributeError, KeyError, etc.)
  - Configuration errors (missing settings, invalid config)
  - Database/backend errors
  - Uncategorized exceptions (fail-fast by default)
"""

from __future__ import annotations

from typeguard import typechecked


class RecoverableError(Exception):
    """Base class for errors that can be safely skipped during asset processing.

    When caught in the asset processing loop, the asset is marked as failed but
    processing continues to the next asset.
    """

    pass


class AlbumNotFoundError(RecoverableError):
    """Raised when an album is deleted or becomes inaccessible during processing."""

    pass


class PermissionDeniedError(RecoverableError):
    """Raised when access to a resource is denied (403 from API)."""

    pass


class AssetDeletedError(RecoverableError):
    """Raised when an asset is deleted during processing."""

    pass


class TemporaryNetworkError(RecoverableError):
    """Raised when a temporary network issue occurs (retry-able)."""

    pass


@typechecked
def categorize_error(exc: Exception) -> tuple[bool, str]:
    """
    Categorizes an exception as recoverable or fatal.

    Returns:
        (is_recoverable: bool, category_name: str)

    Recoverable errors return (True, category_name) - will skip this asset but continue.
    Fatal errors return (False, category_name) - will raise immediately.
    """

    # Check for explicit RecoverableError subclasses
    if isinstance(exc, RecoverableError):
        error_type = type(exc).__name__
        return True, f"Recoverable ({error_type})"

    # Check for API errors in exception message
    exc_str = str(exc)

    # 400/Bad Request - usually album not found or permission issue
    if "400" in exc_str or "Bad Request" in exc_str or "Not found" in exc_str:
        return True, "Recoverable (API 400 - Resource not found)"

    # 403/Forbidden - permission denied
    if "403" in exc_str or "Forbidden" in exc_str or "access" in exc_str.lower():
        return True, "Recoverable (API 403 - Permission denied)"

    # 404/Not Found
    if "404" in exc_str or "not found" in exc_str.lower():
        return True, "Recoverable (API 404 - Asset deleted)"

    # Timeout errors (temporary network issues)
    if any(
        x in type(exc).__name__.lower()
        for x in ["timeout", "connectionerror", "timeouterror"]
    ):
        return True, "Recoverable (Network timeout)"

    # Fatal: Programming errors - fail fast
    if isinstance(
        exc, (AttributeError, KeyError, TypeError, ValueError, IndexError, ImportError)
    ):
        return False, f"Fatal (Programming error: {type(exc).__name__})"

    # Fatal: Configuration errors
    if isinstance(exc, (FileNotFoundError, PermissionError)):
        return False, f"Fatal (Configuration error: {type(exc).__name__})"

    # Fatal: Unknown errors - fail-fast by default (safe default)
    return False, f"Fatal (Uncategorized: {type(exc).__name__})"
