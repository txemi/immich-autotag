from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.config.models import Destination
from immich_autotag.report.modification_entries_list import ModificationEntriesList

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class DestinationWrapper:
    destination: Destination = attrs.field()

    # Here you can add advanced methods for Destination
    def get_tag_names(self) -> list[str]:
        return self.destination.tag_names or []

    def get_album_names(self) -> list[str]:
        return self.destination.album_names or []

    @typechecked
    def apply_action(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> ModificationEntriesList:
        """
        Applies the destination action on the asset_wrapper.
        Adds all destination tags and adds the asset to all destination albums if not already present.
        Returns ModificationEntriesList containing all modifications created during the operation.
        """
        changes = ModificationEntriesList()
        # Add destination tags
        for tag in self.get_tag_names():
            if not asset_wrapper.has_tag(tag_name=tag):
                entries = asset_wrapper.add_tag_by_name(tag_name=tag)
                if entries:
                    changes = changes.extend(entries)
        # Add to destination albums
        for album_name in self.get_album_names():
            if album_name not in asset_wrapper.get_album_names():
                try:
                    from immich_autotag.report.modification_report import (
                        ModificationReport,
                    )

                    context = asset_wrapper.get_context()
                    albums_collection = context.get_albums_collection()
                    album_wrapper = albums_collection.find_first_album_with_name(
                        album_name
                    )
                    if album_wrapper:
                        client = context.get_client_wrapper().get_client()
                        tag_mod_report = ModificationReport.get_instance()
                        entry = album_wrapper.add_asset(
                            asset_wrapper=asset_wrapper,
                            client=client,
                            modification_report=tag_mod_report,
                        )
                        if entry:
                            changes = changes.append(entry)
                    else:
                        # Album not found - log but don't create entry since add_asset wasn't called
                        pass
                except Exception:
                    # Exceptions are already recorded as ModificationEntry objects in add_asset()
                    pass
        return changes

    def __attrs_post_init__(self):
        if not (self.get_tag_names() or self.get_album_names()):
            raise ValueError(
                "DestinationWrapper: destination must have at least one tag or one destination album."
            )
