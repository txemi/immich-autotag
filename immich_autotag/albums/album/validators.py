"""
Validador de tipo para AlbumResponseWrapper.
"""

def validate_album_response_wrapper(instance, attribute, value):
    if value is not None:
        from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
        if not isinstance(value, AlbumResponseWrapper):
            raise TypeError(f"{attribute.name} must be AlbumResponseWrapper or None, not {type(value)}")
