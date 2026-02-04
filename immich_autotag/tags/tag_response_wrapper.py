import attrs

from immich_autotag.api.logging_proxy.types import TagResponseDto
from immich_autotag.types.uuid_wrappers import TagUUID


@attrs.define(auto_attribs=True, slots=True)
class TagWrapper:
    """
    Wrapper for TagResponseDto that allows adding useful methods and properties.
    """

    _tag: TagResponseDto = attrs.field(
        validator=attrs.validators.instance_of(TagResponseDto)
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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TagWrapper):
            return self.get_id() == other.get_id()
        return False

    def __str__(self) -> str:
        return f"TagWrapper(id={self.get_id()}, name={self.get_name()})"
