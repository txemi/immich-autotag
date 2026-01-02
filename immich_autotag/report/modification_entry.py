"""
Clase ModificationEntry: representa una modificación rica (con objetos) en el sistema.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional

import attrs

if TYPE_CHECKING:
    from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper

from immich_autotag.report.serializable_modification_entry import \
    SerializableModificationEntry
from immich_autotag.tags.modification_kind import ModificationKind
from immich_autotag.users.user_response_wrapper import UserResponseWrapper


# class ModificationEntry: ...
@attrs.define(auto_attribs=True, slots=True, frozen=True, kw_only=True)
class ModificationEntry:
    """
    Represents a modification in the system using rich objects (wrappers, DTOs, etc.).
    This class is intended for internal logic, validation, advanced formatting, and access to all high-level data.
    It is not meant for direct persistence or export, but for in-memory manipulation and querying.
    For persistence, export, or printing, convert each instance to SerializableModificationEntry.
    """

    datetime: datetime.datetime = attrs.field(
        validator=attrs.validators.instance_of(datetime.datetime)
    )
    kind: ModificationKind = attrs.field(
        validator=attrs.validators.instance_of(ModificationKind)
    )
    asset_wrapper: Any = attrs.field(default=None)
    tag: Optional["TagResponseWrapper"] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(TagResponseWrapper)),
    )
    album: Optional["AlbumResponseWrapper"] = attrs.field(default=None)
    old_value: Any = attrs.field(default=None)
    new_value: Any = attrs.field(default=None)
    user: Optional[UserResponseWrapper] = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(UserResponseWrapper)
        ),
    )
    extra: Optional[dict[str, Any]] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(dict)),
    )

    def to_serializable(self) -> "SerializableModificationEntry":
        """
        Converts the rich entry to a serializable version (only simple types).
        The link is not stored, but can be derived from asset/album/user if needed.
        """
        album_id = self.album.album.id if self.album is not None else None
        album_name = self.album.album.album_name if self.album is not None else None
        return SerializableModificationEntry(
            datetime=self.datetime.isoformat(),
            kind=self.kind.name,
            asset_id=(
                self.asset_wrapper.id_as_uuid
                if self.asset_wrapper is not None
                else None
            ),
            asset_name=(
                self.asset_wrapper.original_file_name
                if self.asset_wrapper is not None
                else None
            ),
            tag_name=self.tag.tag_name if self.tag is not None else None,
            album_id=album_id,
            album_name=album_name,
            old_value=str(self.old_value) if self.old_value is not None else None,
            new_value=str(self.new_value) if self.new_value is not None else None,
            user_id=self.user.user_id if self.user is not None else None,
            extra=self.extra,
        )
