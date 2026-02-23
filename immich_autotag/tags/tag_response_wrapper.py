import time
from enum import Enum

import attrs

from immich_autotag.api.logging_proxy.types import TagResponseDto
from immich_autotag.types.timestamp import Timestamp
from immich_autotag.types.uuid_wrappers import TagUUID


class TagSource(Enum):
    GET_ALL_TAGS = "get_all_tags"
    GET_TAG_BY_ID = "get_tag_by_id"
    CREATE_TAG = "create_tag"
    ASSET_PAYLOAD = "asset_payload"


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class TagWrapper:
    """
    Wrapper for TagResponseDto that allows adding useful methods and properties.

    Attributes:
        _tag: The TagResponseDto being wrapped.
        source: Optional[str]. Indicates the source of the API call or system that produced this DTO (e.g., 'asset_payload', 'api_call', etc.).
        loaded_at: Optional[float]. Unix timestamp (seconds) of when this DTO was loaded/created in the wrapper.

    Purpose:
        These attributes allow future logic to:
        - Track the provenance of each tag DTO (for debugging, merging, or freshness decisions).
        - Prefer the freshest or most complete DTO when duplicates are encountered.
        - Enable more robust merging and conflict resolution strategies.
    """

    _tag: TagResponseDto = attrs.field(
        init=True,
        validator=attrs.validators.instance_of(TagResponseDto),
        repr=lambda self: f"TagResponseDto(name={self.name})",
    )

    _source: TagSource = attrs.field(init=True, repr=True)
    _loaded_at: Timestamp = attrs.field(
        init=True, factory=lambda: time.time(), repr=True
    )

    def get_id(self) -> TagUUID:
        id_val = self._tag.id
        return TagUUID.from_string(id_val)

    def get_name(self) -> str:
        return self._tag.name

    def name(self) -> str:
        return self.get_name()

    def has_conflict_prefix(self) -> bool:
        """
        Returns True if the tag's name starts with any of the conflict prefixes from config.
        Handles empty string defensively.
        """
        prefixes = self.get_conflict_prefixes()
        name: str = self.name()
        if name == "":
            import logging

            logging.getLogger(__name__).warning(
                f"[TAG MAINTENANCE] Tag with empty name encountered: {self!r}"
            )
            return False
        for prefix in prefixes:
            if name.startswith(prefix):
                return True
        return False

    @staticmethod
    def get_conflict_prefixes() -> list[str]:
        """
        Returns the list of conflict prefixes from config, cleaned and non-empty.
        """
        from immich_autotag.config.manager import ConfigManager

        conf = ConfigManager.get_instance().get_config()
        prefixes = []
        if conf.duplicate_processing is not None:
            prefixes = [
                conf.duplicate_processing.autotag_album_conflict,
                conf.duplicate_processing.autotag_classification_conflict_prefix,
            ]
        return [p for p in prefixes if isinstance(p, str) and p]

    def get_best_tag(self, other: "TagWrapper") -> "TagWrapper":
        """
        Decide which TagWrapper is preferred for merging/updating.

        - If one is from GET_ALL_TAGS and the other is from ASSET_PAYLOAD, prefer GET_ALL_TAGS.
        - If one is from CREATE_TAG and the other is from ASSET_PAYLOAD, prefer CREATE_TAG.
        - If one is from GET_TAG_BY_ID and the other is from ASSET_PAYLOAD, prefer GET_TAG_BY_ID.
        - If both have the same name and one is GET_TAG_BY_ID, prefer GET_TAG_BY_ID.
        - Otherwise, prefer the most recent (highest loaded_at).
        """
        # If self is CREATE_TAG and other is ASSET_PAYLOAD, prefer self
        if (
            self._source == TagSource.CREATE_TAG
            and other._source == TagSource.ASSET_PAYLOAD
        ):
            return self
        # If other is CREATE_TAG and self is ASSET_PAYLOAD, prefer other
        if (
            other._source == TagSource.CREATE_TAG
            and self._source == TagSource.ASSET_PAYLOAD
        ):
            return other
        # If self is GET_ALL_TAGS and other is ASSET_PAYLOAD, prefer self
        if (
            self._source == TagSource.GET_ALL_TAGS
            and other._source == TagSource.ASSET_PAYLOAD
        ):
            return self
        # If other is GET_ALL_TAGS and self is ASSET_PAYLOAD, prefer other
        if (
            other._source == TagSource.GET_ALL_TAGS
            and self._source == TagSource.ASSET_PAYLOAD
        ):
            return other
        # If self is GET_TAG_BY_ID and other is ASSET_PAYLOAD, prefer self
        if (
            self._source == TagSource.GET_TAG_BY_ID
            and other._source == TagSource.ASSET_PAYLOAD
        ):
            return self
        # If other is GET_TAG_BY_ID and self is ASSET_PAYLOAD, prefer other
        if (
            other._source == TagSource.GET_TAG_BY_ID
            and self._source == TagSource.ASSET_PAYLOAD
        ):
            return other
        # If both have the same name and one is GET_TAG_BY_ID, prefer GET_TAG_BY_ID

        self_time = self.get_loaded_at()
        other_time = other.get_loaded_at()
        time_info = ""
        if self_time is not None and other_time is not None:
            if self_time > other_time:
                time_info = f"\n[INFO] 'Self' is more recent by {self_time - other_time:.3f} seconds."
            elif other_time > self_time:
                time_info = f"\n[INFO] 'Other' is more recent by {other_time - self_time:.3f} seconds."
            else:
                time_info = "\n[INFO] Both tags have identical timestamps."
        raise NotImplementedError(
            f"get_best_tag decision logic not implemented yet.\nSelf: {repr(self)}\nOther: {repr(other)}{time_info}"
        )

    def get_loaded_at(self) -> Timestamp:
        """
        Public accessor for the loaded_at timestamp.
        """
        return self._loaded_at
