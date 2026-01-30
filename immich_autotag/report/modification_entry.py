"""
ModificationEntry class: represents a rich modification (with objects) in the system.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional

import attrs

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.serializable_modification_entry import (
    SerializableModificationEntry,
)
from immich_autotag.tags.tag_response_wrapper import TagWrapper
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
    tag: Optional["TagWrapper"] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(TagWrapper)),
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
    progress: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )

    def _get_asset_id(self):
        return self.asset_wrapper.get_id() if self.asset_wrapper is not None else None

    def _get_asset_name(self):
        return (
            str(self.asset_wrapper.get_original_file_name())
            if self.asset_wrapper is not None
            else None
        )

    def _get_tag_name(self):
        return self.tag.get_name() if self.tag is not None else None

    def _get_album_id(self):
        return str(self.album.get_album_uuid()) if self.album is not None else None

    def _get_album_name(self):
        return self.album.get_album_name() if self.album is not None else None

    def _get_old_value(self):
        return str(self.old_value) if self.old_value is not None else None

    def _get_new_value(self):
        return str(self.new_value) if self.new_value is not None else None

    def _get_user_name(self):
        return self.user.name if self.user is not None else None

    def _get_asset_link(self):
        if self.asset_wrapper is not None:
            try:
                return self.asset_wrapper.get_immich_photo_url().geturl()
            except Exception:
                return None
        return None

    def to_serializable(self) -> "SerializableModificationEntry":
        """
        Converts the rich entry to a serializable version (only simple types).
        Calculates asset_link using asset_wrapper.get_immich_photo_url if available.
        """
        return SerializableModificationEntry(
            datetime=self.datetime.isoformat(),
            kind=self.kind.name,
            asset_id=self._get_asset_id(),
            asset_name=self._get_asset_name(),
            tag_name=self._get_tag_name(),
            album_id=self._get_album_id(),
            album_name=self._get_album_name(),
            old_value=self._get_old_value(),
            new_value=self._get_new_value(),
            user_name=self._get_user_name(),
            asset_link=self._get_asset_link(),
            extra=self.extra,
            progress=self.progress,
        )
