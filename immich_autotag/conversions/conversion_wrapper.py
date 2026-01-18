import attrs
from typeguard import typechecked

from immich_autotag.config.models import Conversion, Destination


from immich_autotag.classification.classification_rule_wrapper import ClassificationRuleWrapper

@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class ConversionWrapper:
    conversion: Conversion = attrs.field(
        validator=attrs.validators.instance_of(Conversion)
    )

    @typechecked
    def source_tags(self) -> list[str]:
        return self.conversion.source.tag_names or []

    @typechecked
    def destination_tags(self) -> list[str]:
        return self.conversion.destination.tag_names or []

    @typechecked
    def source_album_patterns(self) -> list[str]:
        return self.conversion.source.album_name_patterns or []

    @typechecked
    def destination_album_patterns(self) -> list[str]:
        return self.conversion.destination.album_name_patterns or []


    @typechecked
    def get_source_wrapper(self) -> ClassificationRuleWrapper:
        """Devuelve un ClassificationRuleWrapper para el source de la conversión."""
        return ClassificationRuleWrapper(self.conversion.source)


    @typechecked
    def get_destination_wrapper(self):
        """Devuelve un DestinationWrapper para el destino de la conversión."""
        return DestinationWrapper(self.conversion.destination)

    # You can add more utility methods as needed
    @typechecked
    def get_single_origin_tag(self) -> str:
        tags = self.source_tags()
        album_patterns = self.source_album_patterns()
        if len(tags) == 1 and not album_patterns:
            return tags[0]
        raise NotImplementedError(
            "Only single-tag origin conversions without album origin are implemented."
        )
