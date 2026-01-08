import attrs
from typeguard import typechecked
from immich_autotag.config.experimental_config.models import Conversion

@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class ConversionWrapper:
    conversion: Conversion = attrs.field(validator=attrs.validators.instance_of(Conversion))

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

    # Puedes añadir más métodos utilitarios según necesidades
