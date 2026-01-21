from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)
from immich_autotag.config.models import Conversion, ConversionMode
from immich_autotag.conversions.destination_wrapper import DestinationWrapper

if TYPE_CHECKING:
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
        return self.conversion.destination.album_names or []

    @typechecked
    def get_source_wrapper(self) -> ClassificationRuleWrapper:
        """Returns a ClassificationRuleWrapper for the conversion source."""
        return ClassificationRuleWrapper(self.conversion.source)

    @typechecked
    def get_destination_wrapper(self) -> DestinationWrapper:
        """Returns a DestinationWrapper for the conversion destination."""
        return DestinationWrapper(self.conversion.destination)

    @typechecked
    def apply_to_asset(self, asset_wrapper: "AssetResponseWrapper") -> list[str]:
        """
        Applies the conversion on the asset_wrapper.
        Uses the source wrapper to check for a match and the destination wrapper to apply the action.
        Removes source tags/albums only if the conversion mode is MOVE.
        """
        match_result = self.get_source_wrapper().matches_asset(asset_wrapper)
        source_matched = match_result is not None and match_result.is_match()
        changes = []
        if source_matched:
            # Applies the destination action (add tags, albums, etc.)
            result_action = self.get_destination_wrapper()
            changes.extend(result_action.apply_action(asset_wrapper))
            # Depending on the conversion mode, removes the source tags/albums
            if self.conversion.mode == ConversionMode.MOVE:
                changes.extend(
                    self.get_source_wrapper().remove_matches(
                        asset_wrapper, match_result
                    )
                )
        return changes
