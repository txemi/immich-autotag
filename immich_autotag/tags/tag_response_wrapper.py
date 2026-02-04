import attrs
import time
from enum import Enum

from immich_autotag.api.logging_proxy.types import TagResponseDto
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

    _tag: TagResponseDto = attrs.field(init=True, validator=attrs.validators.instance_of(TagResponseDto), repr=lambda self: f"TagResponseDto(name={self._tag.name})")

    _source: TagSource = attrs.field(init=True,repr=True)
    _loaded_at: float = attrs.field(init=True, factory=lambda: time.time(), repr=True)

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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TagWrapper):
            return self.get_id() == other.get_id()
        return False



    def get_best_tag(self, other: "TagWrapper") -> "TagWrapper":
        """
        Decide which TagWrapper is preferred for merging/updating.

        Candidate criteria for decision:
        1. Timestamp: Prefer the most recent tag (self._loaded_at vs other._loaded_at).
        2. Source/API: Prefer tags from more authoritative API calls (self._source vs other._source).
        3. Completeness: Prefer the tag with more complete data (e.g., fewer unset fields).

        The actual logic is not implemented yet. This method should be extended to use one or more of these criteria.
        """
        raise NotImplementedError("get_best_tag decision logic not implemented yet")