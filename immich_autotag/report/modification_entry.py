"""
ModificationEntry class: represents a rich modification (with objects) in the system.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional

import attrs

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

from immich_autotag.albums.album.validators import validate_album_response_wrapper

# Import for asset_wrapper type and validator
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.validators import validate_asset_response_wrapper
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
    asset_wrapper: "AssetResponseWrapper | None" = attrs.field(
        default=None,
        validator=attrs.validators.optional(validate_asset_response_wrapper),
    )
    tag: Optional["TagWrapper"] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(TagWrapper)),
    )
    album: Optional["AlbumResponseWrapper"] = attrs.field(
        default=None,
        validator=attrs.validators.optional(validate_album_response_wrapper),
    )
    old_value: Any = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(object)),
    )
    new_value: Any = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(object)),
    )
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

    def to_serializable(self) -> "SerializableModificationEntry":
        """
        Converts the rich entry to a serializable version (only simple types).
        Calculates asset_link using asset_wrapper.get_immich_photo_url if available.
        """
        album_id = str(self.album.get_album_uuid()) if self.album is not None else None
        album_name = self.album.get_album_name() if self.album is not None else None
        asset_link = None
        if self.asset_wrapper is not None:
            try:
                asset_link = self.asset_wrapper.get_immich_photo_url().geturl()
            except Exception:
                asset_link = None
        asset_id = None
        if self.asset_wrapper is not None:
            asset_id_val = self.asset_wrapper.get_id()
            # Convert AssetUUID to uuid.UUID if needed
            if hasattr(asset_id_val, "to_uuid"):
                asset_id = asset_id_val.to_uuid()
            else:
                asset_id = asset_id_val

        asset_name = None
        if self.asset_wrapper is not None:
            asset_name_val = self.asset_wrapper.get_original_file_name()
            # Convert Path to str if needed
            if hasattr(asset_name_val, "__fspath__"):
                asset_name = str(asset_name_val)
            else:
                asset_name = asset_name_val

        return SerializableModificationEntry(
            datetime=self.datetime.isoformat(),
            kind=self.kind.name,
            asset_id=asset_id,
            asset_name=asset_name,
            tag_name=self.tag.get_name() if self.tag is not None else None,
            album_id=album_id,
            album_name=album_name,
            old_value=str(self.old_value) if self.old_value is not None else None,
            new_value=str(self.new_value) if self.new_value is not None else None,
            user_name=self.user.name if self.user is not None else None,
            asset_link=asset_link,
            extra=self.extra,
            progress=self.progress,
        )
