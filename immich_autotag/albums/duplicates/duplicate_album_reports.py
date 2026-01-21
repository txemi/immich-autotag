from typing import Iterator, List, Optional

import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class DuplicateAlbumReport:
    """
    Represents an album duplicate report with explicit references to the two albums involved.
    """

    album_name: str = attrs.field(validator=attrs.validators.instance_of(str))
    existing_album: AlbumResponseWrapper = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseWrapper)
    )
    incoming_album: AlbumResponseWrapper = attrs.field(
        validator=attrs.validators.instance_of(AlbumResponseWrapper)
    )
    note: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )


@attrs.define(auto_attribs=True, slots=True)
class DuplicateAlbumReports:
    """
    Encapsulates the list of album duplicate reports for clearer and safer handling.
    """

    items: List[DuplicateAlbumReport] = attrs.field(
        factory=list, validator=attrs.validators.instance_of(list)
    )

    def append(self, item: DuplicateAlbumReport) -> None:
        self.items.append(item)

    def __iter__(self) -> Iterator[DuplicateAlbumReport]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx) -> DuplicateAlbumReport:
        return self.items[idx]

    def to_list(self) -> List[DuplicateAlbumReport]:
        return list(self.items)

    def clear(self) -> None:
        self.items.clear()
