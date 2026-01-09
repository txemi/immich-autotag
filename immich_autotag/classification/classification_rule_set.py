# Importa la clase MatchResult desde el nuevo archivo
from typing import TYPE_CHECKING, Dict, List

import attrs
from typeguard import typechecked

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)
from immich_autotag.classification.match_result import MatchResult
from immich_autotag.classification.match_result_list import MatchResultList

# Example usage:
# rule_set = get_rule_set_from_config_manager()
# if rule_set.has_tag("autotag_input_meme"):
#     print("Tag exists in rules!")


if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class ClassificationRuleSet:
    rules: List[ClassificationRuleWrapper]

    @typechecked
    def __len__(self) -> int:
        return len(self.rules)

    @typechecked
    def __getitem__(self, idx: int) -> ClassificationRuleWrapper:
        return self.rules[idx]

    @typechecked
    def as_dicts(self) -> List[Dict[str, object]]:
        """Return the rules as a list of dicts (for debugging/logging)."""
        return [wrapper.rule.model_dump() for wrapper in self.rules]

    @typechecked
    def print_rules(self) -> None:
        """Log the current rules using the logging system (level FOCUS)."""
        import pprint

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        rules_str = pprint.pformat(self.as_dicts())
        log(f"Loaded classification rules:\n{rules_str}", level=LogLevel.FOCUS)

    # Add more utility methods as needed for rule matching, filtering, etc.
    @typechecked
    def __has_tag(self, tag_name: str) -> bool:
        """
        Returns True if the given tag_name exists in any rule's tag_names list.
        """
        for wrapper in self.rules:
            if wrapper.has_tag(tag_name):
                return True
        return False

    @staticmethod
    @typechecked
    def get_rule_set_from_config_manager() -> "ClassificationRuleSet":
        """
        Utility to get a ClassificationRuleSet from the experimental config manager singleton.
        """
        from immich_autotag.config.manager import (
            ConfigManager,
        )

        manager = ConfigManager.get_instance()
        if (
            not manager
            or not manager.config
            or not hasattr(manager.config, "classification_rules")
        ):
            raise RuntimeError(
                "ConfigManager or classification_rules not initialized"
            )
        wrappers = [
            ClassificationRuleWrapper(rule)
            for rule in manager.config.classification_rules
        ]
        return ClassificationRuleSet(rules=wrappers)

    @typechecked
    def matches_album(self, album_name: str) -> bool:
        """
        Returns True if the album_name matches any album_name_patterns in any rule.
        """
        # Usar la lógica de MatchResultList para centralizar matches
        for wrapper in self.rules:
            if wrapper.matches_album(album_name):
                return True
        return False

    @typechecked
    def matching_rules(self, asset_wrapper: "AssetResponseWrapper") -> MatchResultList:
        """
        Devuelve un MatchResultList: cada uno indica la regla y el elemento (tag o álbum) que ha macheado.
        """
        asset_tags = set(asset_wrapper.get_tag_names())
        album_names = set(asset_wrapper.get_album_names())
        matches: list[MatchResult] = []
        for wrapper in self.rules:
            # Match por tag
            for tag in asset_tags:
                if wrapper.has_tag(tag):
                    matches.append(MatchResult(rule=wrapper, tag_name=tag))
            # Match por álbum
            for album in album_names:
                if wrapper.matches_album(album):
                    matches.append(MatchResult(rule=wrapper, album_name=album))
        return MatchResultList(matches=matches)
