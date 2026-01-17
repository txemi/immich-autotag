"""
Centralized management of temporary autotag albums.

This module manages all constants and patterns related to temporary albums created
when assets lack a classification. It ensures consistency between album creation
and cleanup operations.

Temporary album naming convention:
    {date}-autotag-temp-unclassified

    Example: 2024-01-15-autotag-temp-unclassified

This pattern allows easy identification and cleanup of temporary assignments.
"""

from typeguard import typechecked

# Shared constants for temporary album naming
AUTOTAG_TEMP_ALBUM_PREFIX = "autotag-temp"
AUTOTAG_TEMP_ALBUM_CATEGORY = "unclassified"


@typechecked
def is_temporary_album(album_name: str) -> bool:
    """
    Checks if an album name follows the temporary album pattern.

    Args:
        album_name: The album name to check.

    Returns:
        True if the album is a temporary album, False otherwise.

    Example:
        >>> is_temporary_album("2024-01-15-autotag-temp-unclassified")
        True
        >>> is_temporary_album("My Family Photos")
        False
    """
    return f"-{AUTOTAG_TEMP_ALBUM_PREFIX}-{AUTOTAG_TEMP_ALBUM_CATEGORY}" in album_name


@typechecked
def get_temporary_album_name(album_date: str) -> str:
    """
    Generates a temporary album name from a date string.

    Args:
        album_date: Date string (typically YYYY-MM-DD format).

    Returns:
        The full temporary album name following the standard pattern.

    Example:
        >>> get_temporary_album_name("2024-01-15")
        '2024-01-15-autotag-temp-unclassified'
    """
    return f"{album_date}-{AUTOTAG_TEMP_ALBUM_PREFIX}-{AUTOTAG_TEMP_ALBUM_CATEGORY}"
