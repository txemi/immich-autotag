import attrs
from typeguard import typechecked

from immich_autotag.config.models import ClassificationRule


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class ClassificationRuleWrapper:
    rule: ClassificationRule = attrs.field(
        validator=attrs.validators.instance_of(ClassificationRule)
    )

    def __attrs_post_init__(self):
        tag_names = self.rule.tag_names
        album_patterns = self.rule.album_name_patterns
        has_tags = bool(tag_names)
        has_albums = bool(album_patterns)
        if has_tags and has_albums:
            raise NotImplementedError(
                f"ClassificationRuleWrapper: Each rule must have either tag_names or a single album_name_pattern, not both. Rule: {self.rule}"
            )
        if not has_tags and not has_albums:
            raise ValueError(
                f"ClassificationRuleWrapper: Each rule must have either tag_names or a single album_name_pattern. Rule: {self.rule}"
            )
        if has_albums:
            if not isinstance(album_patterns, list) or len(album_patterns) != 1:
                raise NotImplementedError(
                    f"ClassificationRuleWrapper: album_name_patterns must be a list with exactly one pattern. Rule: {self.rule}"
                )

    @typechecked
    def has_tag(self, tag_name: str) -> bool:
        return self.rule.tag_names is not None and tag_name in self.rule.tag_names

    @typechecked
    def matches_album(self, album_name: str) -> bool:
        if not self.rule.album_name_patterns:
            return False
        import re

        return any(
            re.match(pattern, album_name) for pattern in self.rule.album_name_patterns
        )

    # You can add more utility methods as needed
