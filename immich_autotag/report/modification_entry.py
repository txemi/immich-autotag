"""
ModificationEntry class: represents a rich modification (with objects) in the system.
"""

from __future__ import annotations

import datetime
import uuid
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

    def _get_tag_name(self) -> Optional[str]:
        """
        Returns the tag name if available, else None.
        """
        return self.tag.get_name() if self.tag is not None else None

    def _get_old_value(self) -> Optional[str]:
        """
        Returns old_value as str if available, else None.
        """
        return str(self.old_value) if self.old_value is not None else None

    def _get_new_value(self) -> Optional[str]:
        """
        Returns new_value as str if available, else None.
        """
        return str(self.new_value) if self.new_value is not None else None

    def _get_user_name(self) -> Optional[str]:
        """
        Returns the user name if available, else None.
        """
        return self.user.name if self.user is not None else None

    def _get_asset_link(self) -> Optional[str]:
        """
        Returns the asset link (asset_link) as str if available, else None.
        """
        if self.asset_wrapper is not None:
            return self.asset_wrapper.get_immich_photo_url().geturl()
        return None

    def _get_album_id(self) -> Optional[str]:
        """
        Returns the album ID as str if available, else None.
        """
        if self.album is not None:
            return str(self.album.get_album_uuid())
        return None

    def _get_album_name(self) -> Optional[str]:
        """
        Returns the album name as str if available, else None.
        """
        if self.album is not None:
            return self.album.get_album_name()
        return None

    def _get_asset_id(self) -> Optional[uuid.UUID]:
        """
        Returns the asset_id as UUID if available, else None.
        """
        if self.asset_wrapper is not None:
            asset_id_val = self.asset_wrapper.get_id()
            return asset_id_val
        return None

    def _get_asset_name(self) -> Optional[str]:
        """
        Returns the asset name as str if available, else None.
        """
        if self.asset_wrapper is not None:
            asset_name_val = self.asset_wrapper.get_original_file_name()
            return str(asset_name_val)
        return None

    def to_serializable(self) -> "SerializableModificationEntry":
        """
        Converts the rich entry to a serializable version (only simple types).
        Calculates asset_link using asset_wrapper.get_immich_photo_url if available.
        """
        album_id = self._get_album_id()
        album_name = self._get_album_name()
        asset_link = self._get_asset_link()

        asset_id = self._get_asset_id()
        asset_name = self._get_asset_name()

        return SerializableModificationEntry(
            datetime=self.datetime.isoformat(),
            kind=self.kind.name,
            asset_id=asset_id,
            asset_name=asset_name,
            tag_name=self._get_tag_name(),
            album_id=album_id,
            album_name=album_name,
            old_value=self._get_old_value(),
            new_value=self._get_new_value(),
            user_name=self._get_user_name(),
            asset_link=asset_link,
            extra=self.extra,
            progress=self.progress,
        )
