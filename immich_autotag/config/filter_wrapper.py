import attr
from typing import Optional, List
from uuid import UUID

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
        Devuelve True si hay filtro_in activo y es un filtro por asset_links concretos (no por tags ni álbumes).
        """
        if not self.filter_config or not self.filter_config.filter_in:
            return False
        ruleset = ClassificationRuleSet(rules=self.filter_config.filter_in)
        return ruleset.is_focused()
    @typechecked
    def get_filter_in_ruleset(self) -> ClassificationRuleSet:
        """
        Devuelve el conjunto de reglas de filtro_in.
        Si no hay configuración, devuelve un conjunto vacío.
        """
        if not self.filter_config:
            raise RuntimeError("FilterConfigWrapper: No filter configuration available.")
        return ClassificationRuleSet(rules=self.filter_config.filter_in)
