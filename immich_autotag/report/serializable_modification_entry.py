"""
SerializableModificationEntry class: serializable version of a modification for persistence/export.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

import attrs
from typeguard import typechecked


# class SerializableModificationEntry: ...
@attrs.define(auto_attribs=True, slots=True, frozen=True, kw_only=True)
class SerializableModificationEntry:
    """
    Represents a modification ready to be persisted, exported, or printed.
    All fields are simple and serializable types (str, UUID, etc.),
    and correspond to the columns of the final table/log.
    This class is immutable and robust, ideal for audit, logs, and exports.
    It is always obtained from ModificationEntry via the to_serializable() method.
    """

    datetime: str = attrs.field(validator=attrs.validators.instance_of(str))
    kind: str = attrs.field(validator=attrs.validators.instance_of(str))
    asset_id: Optional[UUID] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(UUID)),
    )
    asset_name: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    tag_name: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    album_id: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    album_name: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    old_value: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    new_value: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    user_name: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    asset_link: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )
    extra: Optional[dict[str, Any]] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(dict)),
    )
    progress: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )

    @typechecked
    def to_log_string(self) -> str:
        parts = [f"{self.datetime}"]
        parts.append(f"kind={self.kind}")
        # asset_id oculto, ya no se imprime en el log
        if self.asset_link:
            parts.append(f"asset_link={self.asset_link}")
        if self.asset_name:
            parts.append(f"name={self.asset_name}")
        if self.tag_name:
            parts.append(f"tag={self.tag_name}")
        if self.album_id:
            parts.append(f"album_id={self.album_id}")
        if self.album_name:
            parts.append(f"album_name={self.album_name}")
        if self.old_value is not None:
            parts.append(f"old_value={self.old_value}")
        if self.new_value is not None:
            parts.append(f"new_value={self.new_value}")
        if self.user_name:
            parts.append(f"user={self.user_name}")
        if self.extra:
            parts.append(f"extra={self.extra}")
        if self.progress:
            parts.append(f"progress={self.progress}")
        return " | ".join(parts)
