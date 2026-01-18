import attr
from typeguard import typechecked

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)


# Represents the result of a match: reference to the rule and the matched tags and albums
@attr.s(auto_attribs=True, slots=True, kw_only=True, frozen=True)
class MatchResult:
    rule: ClassificationRuleWrapper = attr.ib(
        validator=attr.validators.instance_of(ClassificationRuleWrapper)
    )
    tags_matched: list[str] = attr.ib(
        factory=list,
        validator=attr.validators.instance_of(list),
    )
    albums_matched: list[str] = attr.ib(
        factory=list,
        validator=attr.validators.instance_of(list),
    )

    def __attrs_post_init__(self):
        if not self.tags_matched and not self.albums_matched:
            raise ValueError(
                "MatchResult must have at least one matching tag or album."
            )
    @typechecked
    def has_match(self) -> bool:
        """
        Devuelve True si hay al menos un tag o álbum coincidente en el resultado.
        """
        return bool(self.tags_matched or self.albums_matched)

    @typechecked
    def is_match(self) -> bool:
        """
        Devuelve True si hay al menos un tag o álbum coincidente en el resultado.
        """
        return bool(self.tags_matched or self.albums_matched)
