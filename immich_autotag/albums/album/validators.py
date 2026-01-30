"""
Validador de tipo para AlbumResponseWrapper.
"""

from typing import Any



def validate_album_response_wrapper(instance: Any, attribute: Any, value: Any) -> None:
    if value is not None:
        from immich_autotag.albums.album.album_response_wrapper import (
            AlbumResponseWrapper,
        )

        if not isinstance(value, AlbumResponseWrapper):
            raise TypeError(
                f"{attribute.name} must be AlbumResponseWrapper or None, not {type(value)}"
            )
