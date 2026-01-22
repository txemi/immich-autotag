"""
Health check logic for temporary albums.
"""

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

if TYPE_CHECKING:
    pass


@typechecked
def is_temporary_album_healthy(
    album_wrapper: AlbumResponseWrapper, max_days_apart: int = 30
) -> bool:
    """
    Returns True if all assets in the temporary album are within max_days_apart of each other.
    """
    # Use the wrapper's own methods to get assets
    # We assume context is available via asset_wrapper or globally
    from immich_autotag.context.immich_context import ImmichContext

    context = ImmichContext.get_instance()
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
    album_min_date = album_wrapper._album_dto.start_date
    album_max_date = album_wrapper._album_dto.end_date
    # If album-provided dates exist, compare with calculated
    if album_min_date and album_max_date:
        # Convert to datetime if needed
        if isinstance(album_min_date, str):
            album_min_date = datetime.datetime.fromisoformat(album_min_date)
        if isinstance(album_max_date, str):
            album_max_date = datetime.datetime.fromisoformat(album_max_date)
        # Compare only the date part (ignore time)
        if (
            min_date.date() != album_min_date.date()
            or max_date.date() != album_max_date.date()
        ):
            raise RuntimeError(
                f"Temporary album date mismatch: calculated min/max {min_date.date()} - {max_date.date()} vs album-provided {album_min_date.date()} - {album_max_date.date()}"
            )
        # Use album-provided dates for delta calculation
        delta = (album_max_date - album_min_date).days
    else:
        delta = (max_date - min_date).days
    return delta <= max_days_apart


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
    from immich_autotag.context.immich_context import ImmichContext
    from immich_autotag.report.modification_report import ModificationReport

    album_name = album_wrapper.get_album_name()
    collection = AlbumCollectionWrapper.get_instance()
    client = ImmichContext.get_default_client()
    tag_mod_report = ModificationReport.get_instance()

    collection.delete_album(
        wrapper=album_wrapper,
        client=client,
        tag_mod_report=tag_mod_report,
        reason="Unhealthy temporary album deleted automatically",
    )
    print(f"Deleted unhealthy album: {album_name}")
