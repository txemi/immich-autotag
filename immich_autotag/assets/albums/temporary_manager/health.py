"""
Health check logic for temporary albums.
"""

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

if TYPE_CHECKING:
    pass

# Fix: Add missing import for datetime
import datetime
import enum


# Modes for date source logic in temporary album health check
class TemporaryAlbumDateCheckMode(enum.Enum):
    ALBUM = "album"  # Trust album-provided dates
    ASSETS = "assets"  # Trust asset-calculated dates
    DEVELOPER = "developer"  # Compare both and raise if mismatch


@typechecked
def is_temporary_album_healthy(
    album_wrapper: AlbumResponseWrapper,
    max_days_apart: int = 30,
    date_check_mode: "TemporaryAlbumDateCheckMode" = TemporaryAlbumDateCheckMode.ALBUM,
) -> bool:
    """
    Returns True if all assets in the temporary album are within max_days_apart of each other.
    """
    # Use the wrapper's own methods to get assets
    # We assume context is available via asset_wrapper or globally
    from immich_autotag.context.immich_context import ImmichContext

    context = ImmichContext.get_default_instance()
    assets = album_wrapper.wrapped_assets(context)
    if not assets or len(assets) < 2:
        return True
    # Calculate min/max from assets
    dates = [date for date in (a.get_best_date() for a in assets) if date is not None]
    if len(dates) < 2:
        return True
    min_date = min(dates)
    max_date = max(dates)
    # Try to get album-provided min/max dates if available
    album_min_date = album_wrapper.get_start_date()
    album_max_date = album_wrapper.get_end_date()

    # Logic based on mode
    if date_check_mode == TemporaryAlbumDateCheckMode.ALBUM:
        # Trust album-provided dates if available, else fallback to assets
        if album_min_date and album_max_date:
            if isinstance(album_min_date, str):
                album_min_date = datetime.datetime.fromisoformat(album_min_date)
            if isinstance(album_max_date, str):
                album_max_date = datetime.datetime.fromisoformat(album_max_date)
            delta = (album_max_date - album_min_date).days
        else:
            delta = (max_date - min_date).days
        return delta <= max_days_apart
    elif date_check_mode == TemporaryAlbumDateCheckMode.ASSETS:
        # Always use asset-calculated dates
        delta = (max_date - min_date).days
        return delta <= max_days_apart
    elif date_check_mode == TemporaryAlbumDateCheckMode.DEVELOPER:
        # Compare both, allow 1 day diff, raise if mismatch
        if album_min_date and album_max_date:
            if isinstance(album_min_date, str):
                album_min_date = datetime.datetime.fromisoformat(album_min_date)
            if isinstance(album_max_date, str):
                album_max_date = datetime.datetime.fromisoformat(album_max_date)
            min_diff = abs((min_date.date() - album_min_date.date()).days)
            max_diff = abs((max_date.date() - album_max_date.date()).days)
            if min_diff > 1 or max_diff > 1:
                raise RuntimeError(
                    f"Temporary album date mismatch: calculated min/max {min_date.date()} - {max_date.date()} vs album-provided {album_min_date.date()} - {album_max_date.date()} (allowed diff: 1 day)"
                )
            delta = (album_max_date - album_min_date).days
        else:
            delta = (max_date - min_date).days
        return delta <= max_days_apart
    else:
        raise ValueError(f"Unknown TemporaryAlbumDateCheckMode: {date_check_mode}")


@typechecked
def cleanup_unhealthy_album(
    album_wrapper: AlbumResponseWrapper,
):
    """
    Deletes the album if it is unhealthy.
    """
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )
    from immich_autotag.report.modification_report import ModificationReport

    album_name = album_wrapper.get_album_name()
    collection = AlbumCollectionWrapper.get_instance()
    from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

    client = ImmichClientWrapper.get_default_instance()
    tag_mod_report = ModificationReport.get_instance()

    collection.delete_album(
        wrapper=album_wrapper,
        client=client.get_client(),
        tag_mod_report=tag_mod_report,
        reason="Unhealthy temporary album deleted automatically",
    )
    print(f"Deleted unhealthy album: {album_name}")
