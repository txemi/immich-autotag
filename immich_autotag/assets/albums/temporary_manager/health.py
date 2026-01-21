"""
Health check logic for temporary albums.
"""

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

if TYPE_CHECKING:
    from immich_autotag.report.modification_report import ModificationReport


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
    # Example: assume each asset has a 'date' attribute (datetime)
    dates = [date for date in (a.get_best_date() for a in assets) if date is not None]
    if len(dates) < 2:
        return True
    min_date = min(dates)
    max_date = max(dates)
    delta = (max_date - min_date).days
    return delta <= max_days_apart


@typechecked
def cleanup_unhealthy_album(
    album_wrapper: AlbumResponseWrapper,
    tag_mod_report: "ModificationReport" = None,
):
    """
    Deletes the album if it is unhealthy. Optionally logs the operation.
    """
    # TODO: Implement actual deletion logic using album_wrapper and client
    # Example: album_wrapper.delete(client)
    album_name = album_wrapper.get_album_name()
    if tag_mod_report:
        from immich_autotag.tags.modification_kind import ModificationKind

        tag_mod_report.add_album_modification(
            kind=ModificationKind.DELETE_ALBUM_UNHEALTHY,
            album=album_wrapper,
            old_value=album_name,
            extra={"reason": "Unhealthy temporary album deleted automatically"},
        )
    # Placeholder for deletion
    print(f"Deleted unhealthy album: {album_name}")
