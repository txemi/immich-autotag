# Imports the MatchResult class from the new file
from typing import TYPE_CHECKING, Dict, List

import attrs
from typeguard import typechecked

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)
from immich_autotag.classification.match_result import MatchResult
from immich_autotag.classification.match_result_list import MatchResultList
from immich_autotag.context.immich_context import ImmichContext

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

        wrappers = [
            ClassificationRuleWrapper(rule)
            for rule in manager.config.classification.rules
        ]
        return ClassificationRuleSet(rules=wrappers)

    @typechecked
    def matches_album(self, album_name: str) -> bool:
        """
        Returns True if the album_name matches any album_name_patterns in any rule.
        """
        # Use MatchResultList logic to centralize matches
        for wrapper in self.rules:
            if wrapper.matches_album(album_name):
                return True
        return False

    @typechecked
    def matching_rules(self, asset_wrapper: "AssetResponseWrapper") -> MatchResultList:
        """
        Returns a MatchResultList: each one indicates the rule and the element (tag or album) that matched.
        """
        matches: list[MatchResult] = []
        for wrapper in self.rules:
            match = wrapper.matches_asset(asset_wrapper)
            if match is not None:
                matches.append(match)
        return MatchResultList(matches=matches)

    @typechecked
    def is_focused(self) -> bool:
        """
        Returns True when any rule in the set targets concrete assets via `asset_links`.
        Filtering by tags or albums alone does not count as focused.
        """
        for wrapper in self.rules:
            if wrapper.is_focused():
                return True
        return False

    @typechecked
    def matches_any_album_of_asset(self, asset_wrapper: "AssetResponseWrapper") -> bool:
        """
        Returns True if any album name of the asset matches any album_name_patterns in any rule.
        """
        for album_name in asset_wrapper.get_album_names():
            if self.matches_album(album_name):
                return True
        return False

    @typechecked
    def get_filtered_in_assets_by_uuid(
        self, context: "ImmichContext"
    ) -> List["AssetResponseWrapper"]:
        """
        Extracts all UUIDs from asset_links of all rules,
        loads the assets from the API and returns the list of AssetResponseWrapper.
        """
        from uuid import UUID

        all_uuids: List[UUID] = []
        for wrapper in self.rules:
            all_uuids.extend(wrapper.extract_uuids_from_asset_links())

        if not all_uuids:
            return []

        # Load assets from the API
        from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

        wrappers: List[AssetResponseWrapper] = []

        for asset_uuid in all_uuids:
            wrapper = context.asset_manager.get_asset(asset_uuid, context)
            if wrapper is None:
                raise RuntimeError(
                    f"[ERROR] Asset with ID {asset_uuid} could not be loaded from API."
                )
            wrappers.append(wrapper)

        print(
            f"[INFO] Filtered mode: Only processing {len(wrappers)} asset(s) from filter rules."
        )
        return wrappers
