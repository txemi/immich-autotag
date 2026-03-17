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
from urllib.parse import ParseResult

from typeguard import typechecked


class RecoverableError(Exception):
    """Base class for errors that can be safely skipped during asset processing.

    When caught in the asset processing loop, the asset is marked as failed but
    processing continues to the next asset.
    """

    pass


class ImmichApiError(RecoverableError):
    """Base class for API errors from Immich server, enriched with context URLs."""

    def _format_message(self) -> str:
        """Format error message with context URLs."""
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.album_url:
            parts.append(f"\nAlbum URL: {self.album_url.geturl()}")
        if self.asset_url:
            parts.append(f"\nAsset URL: {self.asset_url.geturl()}")
        if self.response_content:
            parts.append(f"\nAPI Response: {self.response_content}")
        return " ".join(parts)

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_content: str | None = None,
        album_url: ParseResult | None = None,
        asset_url: ParseResult | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_content = response_content
        self.album_url = album_url
        self.asset_url = asset_url
        super().__init__(self._format_message())


class AlbumNotFoundError(ImmichApiError):
    """Raised when an album is deleted or becomes inaccessible during processing (400/404)."""

    pass


class PermissionDeniedError(ImmichApiError):
    """Raised when access to a resource is denied (403 from API)."""

    pass


class RemoveAssetFromAlbumApiError(ImmichApiError):
    """Raised when the Immich API returns an error response while removing an asset from an album.

    This is a recoverable error: the asset processing loop can catch it, log a warning,
    and continue to the next asset instead of crashing the entire run.

    Typical causes:
    - ``not_found``: the asset is no longer part of the album (stale cache).
    - ``no_permission``: the authenticated user lost access to the album.
    """

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

    # 5xx/Server errors - temporary server issues (recoverable)
    if (
        "500" in exc_str
        or "501" in exc_str
        or "502" in exc_str
        or "503" in exc_str
        or "504" in exc_str
        or "Internal Server Error" in exc_str
        or "Bad Gateway" in exc_str
        or "Service Unavailable" in exc_str
        or "Gateway Timeout" in exc_str
    ):
        return CategorizedError(True, "Recoverable (API 5xx - Temporary server error)")

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
