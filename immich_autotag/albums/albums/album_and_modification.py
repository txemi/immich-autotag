from typing import Optional

import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_entry import ModificationEntry


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumAndModification:
    album: Optional[AlbumResponseWrapper] = None
    modification: Optional[ModificationEntry] = None
