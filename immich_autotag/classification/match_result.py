import attr

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)


# Represents the result of a match: reference to the rule and the matched element (tag or album)
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
                f"MatchResult must have either tag_name or album_name, but not both or neither. tag_name={self.tag_name}, album_name={self.album_name}"
            )
