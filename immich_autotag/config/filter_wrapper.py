from typing import Optional

import attr
from typeguard import typechecked

from immich_autotag.classification.classification_rule_set import ClassificationRuleSet

from .models import FilterConfig


@attr.s(auto_attribs=True, kw_only=True)
class FilterConfigWrapper:
    filter_config: Optional[FilterConfig] = None

    @classmethod
    def from_filter_config(cls, filter_config: Optional[FilterConfig]):
        return cls(filter_config=filter_config)

    @typechecked
    def is_focused(self) -> bool:
        """
        Returns True if there is an active filter_in and it is a filter by specific asset_links (not by tags or albums).
        """
        if not self.filter_config or not self.filter_config.filter_in:
            return False
        return self.get_filter_in_ruleset().is_focused()

    @typechecked
    def get_filter_in_ruleset(self) -> ClassificationRuleSet:
        """
        Returns a ClassificationRuleSet with the filter_in rules.
        """
        if not self.filter_config or not self.filter_config.filter_in:
            from immich_autotag.classification.classification_rule_wrapper import (
                ClassificationRuleWrapper,
            )

            return ClassificationRuleSet(rules=[])

        from immich_autotag.classification.classification_rule_wrapper import (
            ClassificationRuleWrapper,
        )

        wrappers = [
            ClassificationRuleWrapper(rule) for rule in self.filter_config.filter_in
        ]
        return ClassificationRuleSet(rules=wrappers)
