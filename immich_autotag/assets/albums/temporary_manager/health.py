"""
Health check logic for temporary albums.
"""

def is_temporary_album_healthy(album_wrapper) -> bool:

from typeguard import typechecked

@typechecked
def is_temporary_album_healthy(album_wrapper, max_days_apart: int = 30) -> bool:
    """
    Returns True if all assets in the temporary album are within max_days_apart of each other.
    """
    # TODO: Implement real date extraction from assets
    assets = getattr(album_wrapper.album, 'assets', [])
    if not assets or len(assets) < 2:
        return True
    # Example: assume each asset has a 'date' attribute (datetime)
    dates = [getattr(a, 'date', None) for a in assets if getattr(a, 'date', None)]
    if len(dates) < 2:
        return True
    min_date = min(dates)
    max_date = max(dates)
    delta = (max_date - min_date).days
    return delta <= max_days_apart

@typechecked
def cleanup_unhealthy_album(album_wrapper, client, tag_mod_report=None):
    """
    Deletes the album if it is unhealthy. Optionally logs the operation.
    """
    # TODO: Implement actual deletion logic using album_wrapper and client
    # Example: album_wrapper.delete(client)
    if tag_mod_report:
        tag_mod_report.add_album_modification(
            kind="DELETE_ALBUM_UNHEALTHY",
            album=album_wrapper,
            old_value=album_wrapper.album.album_name,
            extra={"reason": "Unhealthy temporary album deleted automatically"},
        )
    # Placeholder for deletion
    print(f"Deleted unhealthy album: {album_wrapper.album.album_name}")
