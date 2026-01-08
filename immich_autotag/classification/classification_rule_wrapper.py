import attrs
from typeguard import typechecked
from immich_autotag.config.experimental_config.models import ClassificationRule

@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class ClassificationRuleWrapper:
    rule: ClassificationRule = attrs.field(validator=attrs.validators.instance_of(ClassificationRule))

    @typechecked
    def has_tag(self, tag_name: str) -> bool:
        return self.rule.tag_names is not None and tag_name in self.rule.tag_names

    @typechecked
    def matches_album(self, album_name: str) -> bool:
        if not self.rule.album_name_patterns:
            return False
        import re
        return any(re.match(pattern, album_name) for pattern in self.rule.album_name_patterns)

    # Puedes añadir más métodos utilitarios según necesidades
