from typing import List

import attrs

from immich_autotag.config.manager import ConfigManager
from immich_autotag.conversions.conversion_wrapper import ConversionWrapper


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class TagConversions:
    _conversions: List[ConversionWrapper]

    @staticmethod
    def from_config_manager() -> "TagConversions":
        config_manager = ConfigManager.get_instance()
        config = config_manager.config
        if not config or not hasattr(config, "conversions"):
            raise RuntimeError("No conversions found in configuration.")
        wrappers = [ConversionWrapper(conv) for conv in config.conversions]
        return TagConversions(wrappers)

    def get_all(self) -> List[ConversionWrapper]:
        return self._conversions

    # Utility methods for searching, filtering, etc. can be added here
    def __iter__(self):
        return iter(self._conversions)
