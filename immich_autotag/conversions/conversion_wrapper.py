
import attrs
from typeguard import typechecked
from typing import TYPE_CHECKING

from immich_autotag.config.models import Conversion, Destination, ConversionMode
from immich_autotag.classification.classification_rule_wrapper import ClassificationRuleWrapper

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

# Import normal para ejecución (evita NameError en tiempo de ejecución)
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

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

    @typechecked
    def apply_to_asset(self, asset_wrapper: "AssetResponseWrapper") -> list[str]:
        """
        Aplica la conversión sobre el asset_wrapper.
        Utiliza el wrapper de origen para comprobar el match y el de destino para aplicar la acción.
        Elimina los tags/álbumes de origen solo si el modo de conversión es MOVE.
        """
        match_result = self.get_source_wrapper().matches_asset(asset_wrapper)
        source_matched = match_result is not None and match_result.is_match()
        changes = []
        if source_matched:
            # Aplica la acción de destino (añadir etiquetas, álbumes, etc.)
            result_action = self.get_destination_wrapper()
            changes.extend(result_action.apply_action(asset_wrapper))
            # Según el modo de conversión, elimina los tags/álbumes de origen
            if self.conversion.mode == ConversionMode.MOVE:
                changes.extend(self.get_source_wrapper().remove_matches(asset_wrapper, match_result))
        return changes

