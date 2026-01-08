# Example usage:
# rule_set = get_rule_set_from_config_manager()
# if rule_set.has_tag("autotag_input_meme"):
#     print("Tag exists in rules!")

from typing import List

import attrs
from typeguard import typechecked

from immich_autotag.config.experimental_config.models import ClassificationRule


@attrs.define(auto_attribs=True, slots=True, kw_only=True)
class ClassificationRuleSet:

    rules: List[ClassificationRule]

    @typechecked
    def __len__(self) -> int:
        return len(self.rules)

    @typechecked
    def __getitem__(self, idx: int) -> ClassificationRule:
        return self.rules[idx]

    @typechecked
    def as_dicts(self) -> List[dict]:
        """Return the rules as a list of dicts (for debugging/logging)."""
        return [rule.model_dump() for rule in self.rules]

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
    def has_tag(self, tag_name: str) -> bool:
        """
        Returns True if the given tag_name exists in any rule's tag_names list.
        """
        for rule in self.rules:
            if rule.tag_names and tag_name in rule.tag_names:
                return True
        return False

    @staticmethod
    @typechecked
    def get_rule_set_from_config_manager() -> "ClassificationRuleSet":
        """
        Utility to get a ClassificationRuleSet from the experimental config manager singleton.
        """
        from immich_autotag.config.experimental_config.manager import \
            ExperimentalConfigManager

        manager = ExperimentalConfigManager.get_instance()
        if (
            not manager
            or not manager.config
            or not hasattr(manager.config, "classification_rules")
        ):
            raise RuntimeError(
                "ExperimentalConfigManager or classification_rules not initialized"
            )
        return ClassificationRuleSet(rules=manager.config.classification_rules)
    @typechecked
    def matches_album(self, album_name: str) -> bool:
        """
        Returns True if the album_name matches any album_name_patterns in the rules.
        """
        for rule in self.rules:
            patterns = getattr(rule, "album_name_patterns", None)
            if patterns:
                for pattern in patterns:
                    if re.match(pattern, album_name):
                        return True
        return False