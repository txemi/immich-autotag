import attr

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)


# Representa el resultado de un match: referencia a la regla y al elemento macheado (tag o álbum)
@attr.s(auto_attribs=True, slots=True, kw_only=True, frozen=True)
class MatchResult:
    rule: ClassificationRuleWrapper = attr.ib(
        validator=attr.validators.instance_of(ClassificationRuleWrapper)
    )
    tag_name: str = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    album_name: str = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    def __attrs_post_init__(self):
        has_tag = self.tag_name is not None
        has_album = self.album_name is not None
        if has_tag == has_album:
            raise ValueError(
                f"MatchResult debe tener o tag_name o album_name, pero no ambos ni ninguno. tag_name={self.tag_name}, album_name={self.album_name}"
            )
