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

from dataclasses import dataclass

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


@dataclass
class CategorizedError:
    is_recoverable: bool
    category_name: str


@typechecked
def categorize_error(exc: Exception) -> CategorizedError:
    """
    Categorizes an exception as recoverable or fatal.

    Returns:
        CategorizedError: with is_recoverable and category_name fields.

    Recoverable errors return CategorizedError(is_recoverable=True, ...)
    Fatal errors return CategorizedError(is_recoverable=False, ...)
    """

    # Check for explicit RecoverableError subclasses
    if isinstance(exc, RecoverableError):
        error_type = type(exc).__name__
        return CategorizedError(True, f"Recoverable ({error_type})")

    # Check for API errors in exception message
    exc_str = str(exc)

    # 400/Bad Request - usually album not found or permission issue
    if "400" in exc_str or "Bad Request" in exc_str or "Not found" in exc_str:
        return CategorizedError(True, "Recoverable (API 400 - Resource not found)")

    # 403/Forbidden - permission denied
    if "403" in exc_str or "Forbidden" in exc_str or "access" in exc_str.lower():
        return CategorizedError(True, "Recoverable (API 403 - Permission denied)")

    # 404/Not Found
    if "404" in exc_str or "not found" in exc_str.lower():
        return CategorizedError(True, "Recoverable (API 404 - Asset deleted)")

    # Timeout errors (temporary network issues)
    if any(
        x in type(exc).__name__.lower()
        for x in ["timeout", "connectionerror", "timeouterror"]
    ):
        return CategorizedError(True, "Recoverable (Network timeout)")

    # Fatal: Programming errors - fail fast
    if isinstance(
        exc, (AttributeError, KeyError, TypeError, ValueError, IndexError, ImportError)
    ):
        return CategorizedError(
            False, f"Fatal (Programming error: {type(exc).__name__})"
        )

    # Fatal: Configuration errors
    if isinstance(exc, (FileNotFoundError, PermissionError)):
        return CategorizedError(
            False, f"Fatal (Configuration error: {type(exc).__name__})"
        )

    # Fatal: Unknown errors - fail-fast by default (safe default)
    return CategorizedError(False, f"Fatal (Uncategorized: {type(exc).__name__})")
