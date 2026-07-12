from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.classification.classification_rule_wrapper import (
    ClassificationRuleWrapper,
)

# Error handling mode import
from immich_autotag.config.models import Conversion, ConversionMode
from immich_autotag.conversions.destination_wrapper import DestinationWrapper
from immich_autotag.report.modification_entries_list import ModificationEntriesList

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
    def apply_to_asset(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> ModificationEntriesList:
        """
        Applies the conversion on the asset_wrapper.
        Uses the source wrapper to check for a match and the destination wrapper to apply the action.
        Removes source tags/albums only if the conversion mode is MOVE.
        Returns ModificationEntriesList containing all modifications created during the operation.
        """
        match_result = self.get_source_wrapper().matches_asset(asset_wrapper)
        source_matched = match_result is not None and match_result.is_match()
        changes = ModificationEntriesList()
        if source_matched:
            # Applies the destination action (add tags, albums, etc.)
            result_action = self.get_destination_wrapper()
            action_changes = result_action.apply_action(asset_wrapper)
            changes = changes.extend(action_changes)
            # Depending on the conversion mode, removes the source tags/albums
            if self.conversion.mode == ConversionMode.MOVE and match_result is not None:
                destination_albums = result_action.get_album_names()
                if destination_albums:
                    # Only remove source tags if all destination albums are now in the asset's
                    # album membership. If any album was not found/created, keep the source tag
                    # so the asset retains its classification signal on future runs.
                    current_album_names = set(asset_wrapper.get_album_names())
                    all_destinations_resolved = all(
                        album_name in current_album_names
                        for album_name in destination_albums
                    )
                    if all_destinations_resolved:
                        self.get_source_wrapper().remove_matches(
                            asset_wrapper, match_result, remove_source_albums=False
                        )
                    else:
                        from immich_autotag.logging.levels import LogLevel
                        from immich_autotag.logging.utils import log

                        missing = [
                            a
                            for a in destination_albums
                            if a not in current_album_names
                        ]
                        log(
                            f"[CONVERSION] Skipping source tag removal for "
                            f"'{asset_wrapper.get_original_file_name()}': destination album(s) "
                            f"{missing} not resolved. Classification signal preserved.",
                            level=LogLevel.WARNING,
                        )
                else:
                    # Pure tag-to-tag conversion: no album involved, remove source tags unconditionally.
                    self.get_source_wrapper().remove_matches(
                        asset_wrapper, match_result, remove_source_albums=False
                    )
        return changes
