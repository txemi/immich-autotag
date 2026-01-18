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

    @typechecked
    def apply_to_asset(self, asset_wrapper: "AssetResponseWrapper") -> list[str]:
        """
        Aplica la conversión sobre el asset_wrapper.
        La lógica se mueve aquí desde AssetResponseWrapper.
        """
        match_result=self.get_source_wrapper().matches_asset(asset_wrapper)
        has_origin= match_result is not None and match_result.is_match()
        result_action=self.get_destination_wrapper()
        dest_tags = self.destination_tags()
        if len(dest_tags) != 1:
            raise NotImplementedError("Only single destination tag conversions are implemented.")
        dest_tag = dest_tags[0]

        has_dest = asset_wrapper.has_tag(dest_tag)
        changes = []
        if has_origin and not has_dest:
            try:
                asset_wrapper.add_tag_by_name(dest_tag)
                changes.append(f"Added tag '{dest_tag}' and removed '{origin_tag}'")
            except Exception as e:
                changes.append(f"Failed to add '{dest_tag}', removed '{origin_tag}'")
            asset_wrapper.remove_tag_by_name(origin_tag)
        elif has_origin and has_dest:
            asset_wrapper.remove_tag_by_name(origin_tag)
            changes.append(f"Removed redundant tag '{origin_tag}' (already had '{dest_tag}')")
        return changes

