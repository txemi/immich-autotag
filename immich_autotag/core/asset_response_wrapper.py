from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from immich_client.models.asset_response_dto import AssetResponseDto
from typeguard import typechecked

from immich_autotag.config.user import CLASSIFIED_TAGS, ALBUM_PATTERN, AUTOTAG_UNKNOWN_CATEGORY, AUTOTAG_CATEGORY_CONFLICT
from .match_classification_result import MatchClassificationResult

if TYPE_CHECKING:
    from .immich_context import ImmichContext
    from .main import TagModificationReport




@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AssetResponseWrapper:
    asset: AssetResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseDto)
    )
    context: "ImmichContext" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )

    def __attrs_post_init__(self):
        # Avoid direct reference to ImmichContext to prevent NameError/circular import
        if self.context.__class__.__name__ != "ImmichContext":
            raise TypeError(f"context must be ImmichContext, not {type(self.context)}")

    @typechecked
    def has_tag(self, tag_name: str) -> bool:
        """
        Returns True if the asset has the tag with that name (case-insensitive).
        """
        return (
            any(tag.name.lower() == tag_name.lower() for tag in self.asset.tags)
            if self.asset.tags
            else False
        )

    @typechecked
    def remove_tag_by_name(
        self,
        tag_name: str,
        verbose: bool = True,
        tag_mod_report: "TagModificationReport | None" = None,
        user: str | None = None,
    ) -> bool:
        """
        Removes all tags from the asset with the given name (case-insensitive), even if they have different IDs (e.g., global and nested tags).
        Returns True if at least one was removed, False if none were found.
        After removal, reloads the asset and checks if the tag is still present. Raises if any remain.
        """
        from immich_client.api.assets import get_asset_info
        from immich_client.api.tags import untag_assets
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        # Find all tag objects on the asset with the given name (case-insensitive)
        tags_to_remove = [
            tag for tag in self.asset.tags if tag.name.lower() == tag_name.lower()
        ]
        if not tags_to_remove:
            if verbose:
                print(f"[INFO] Asset id={self.id} does not have the tag '{tag_name}'")
            return False

        print(
            f"[DEBUG] Before removal: asset.id={self.id}, asset_name={self.original_file_name}, tag_name='{tag_name}', tag_ids={[tag.id for tag in tags_to_remove]}"
        )
        print(f"[DEBUG] Tags before removal: {self.get_tag_names()}")

        removed_any = False
        for tag in tags_to_remove:
            response = untag_assets.sync(
                id=tag.id, client=self.context.client, body=BulkIdsDto(ids=[self.id])
            )
            print(f"[DEBUG] Full untag_assets response for tag_id={tag.id}: {response}")
            if verbose:
                print(
                    f"[INFO] Removed tag '{tag_name}' (id={tag.id}) from asset.id={self.id}. Response: {response}"
                )
            removed_any = True
            if tag_mod_report:
                tag_mod_report.add_modification(
                    asset_id=self.id,
                    asset_name=self.original_file_name,
                    action="remove",
                    tag_name=tag_name,
                    user=user,
                )

        # Reload asset and check if tag is still present
        updated_asset = get_asset_info.sync(id=self.id, client=self.context.client)
        object.__setattr__(self, "asset", updated_asset)
        print(f"[DEBUG] Tags after removal: {self.get_tag_names()}")
        tag_still_present = self.has_tag(tag_name)
        if tag_still_present:
            if tag_mod_report:
                tag_mod_report.add_modification(
                    asset_id=self.id,
                    asset_name=self.original_file_name,
                    action="warning_removal_failed",
                    tag_name=tag_name,
                    user=user,
                )
            error_msg = f"[ERROR] Tag '{tag_name}' could NOT be removed from asset.id={self.id} ({self.original_file_name}). Still present after API call."
            print(error_msg)
            raise RuntimeError(error_msg)
        return removed_any

    @typechecked
    def add_tag_by_name(
        self,
        tag_name: str,
        verbose: bool = False,
        info: bool = True,
        tag_mod_report: "TagModificationReport | None" = None,
        user: str | None = None,
    ) -> bool:
        """
        Adds a tag to the asset by name using the Immich API if it doesn't have it already.
        Returns True if added, raises exception if it already had it or if the tag doesn't exist.
        """
        from immich_client.api.tags import tag_assets
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        tag = self.context.tag_collection.find_by_name(tag_name)
        if tag is None:
            tag = self.context.tag_collection.create_tag_if_not_exists(
                tag_name, self.context.client
            )
        # Check if the asset already has the tag
        if self.has_tag(tag_name):
            raise ValueError(f"[INFO] Asset.id={self.id} already has tag '{tag_name}'")
        # Call the correct endpoint to associate the tag with the asset
        if verbose:
            print(
                f"[DEBUG] Calling tag_assets.sync with tag_id={tag.id} and asset_id={self.id}"
            )
        response = tag_assets.sync(
            id=tag.id, client=self.context.client, body=BulkIdsDto(ids=[self.id])
        )
        if verbose:
            print(f"[DEBUG] Response tag_assets: {response}")
        # Request the asset again and check if the tag is applied
        updated_asset = get_asset_info.sync(id=self.id, client=self.context.client)
        if verbose:
            print(f"[DEBUG] Asset after tag_assets: {updated_asset}")
        tag_names = (
            [tag.name for tag in updated_asset.tags] if updated_asset.tags else []
        )
        if tag_name not in tag_names:
            raise RuntimeError(
                f"[ERROR] Tag '{tag_name}' doesn't appear in the asset after update. Current tags: {tag_names}"
            )
        if info:
            print(
                f"[INFO] Added tag '{tag_name}' to asset.id={self.id}. Current tags: {tag_names}"
            )
        if tag_mod_report:
            tag_mod_report.add_modification(
                asset_id=self.id,
                asset_name=self.original_file_name,
                action="add",
                tag_name=tag_name,
                user=user,
            )
        return True

    @typechecked
    def _get_current_tag_ids(self) -> list[str]:
        """Returns the IDs of the asset's current tags."""
        # No longer using getattr, accessing self.asset.tags directly
        return [t.id for t in self.asset.tags]

    @typechecked
    def get_album_names(self) -> list[str]:
        """
        Returns the names of the albums this asset belongs to.
        """
        return self.context.albums_collection.albums_for_asset(self.asset)

    @typechecked
    def get_tag_names(self) -> list[str]:
        """
        Returns the names of the tags associated with this asset.
        """
        return [tag.name for tag in self.asset.tags] if self.asset.tags else []

    @typechecked
    def is_asset_classified(self) -> bool:
        """
        Returns True if the asset meets any classification condition:
        - Has any of the tags in CLASSIFIED_TAGS.
        - Belongs to an album whose name matches ALBUM_PATTERN.
        """
        import re

        # Check tags
        asset_tags = self.get_tag_names()
        for tag in asset_tags:
            if tag.lower() in [t.lower() for t in CLASSIFIED_TAGS]:
                return True

        # Check albums
        album_names = self.get_album_names()
        for name in album_names:
            if re.match(ALBUM_PATTERN, name):
                return True

        return False

    @property
    def original_file_name(self) -> str:
        return self.asset.original_file_name

    @property
    def is_favorite(self) -> bool:
        return self.asset.is_favorite

    @property
    def created_at(self) -> str:
        return self.asset.created_at

    @property
    def id(self) -> str:
        return self.asset.id

    @property
    def original_path(self) -> str:
        return self.asset.original_path

    @typechecked
    def get_classification_match_detail(self) -> MatchClassificationResult:
        """
        Returns an object with the detail of the tags and albums that matched classification.
        """
        import re

        tags_matched = []
        albums_matched = []
        # Tags
        asset_tags = self.get_tag_names()
        for tag in asset_tags:
            if tag.lower() in [t.lower() for t in CLASSIFIED_TAGS]:
                tags_matched.append(tag)
        # Albums
        album_names = self.get_album_names()
        for name in album_names:
            if re.match(ALBUM_PATTERN, name):
                albums_matched.append(name)
        return MatchClassificationResult(
            tags_matched=tags_matched, albums_matched=albums_matched
        )

    @typechecked
    def check_unique_classification(self, fail_fast: bool = True) -> bool:
        """
        Checks if the asset is classified by more than one criterion (tag or album).
        Now considers conflict if the total number of matching tags and albums is greater than 1.
        If fail_fast is True (default), raises an exception. If False, logs a warning only.
        Returns True if there is a conflict (multiple criteria), False otherwise.
        """
        match_detail = self.get_classification_match_detail()
        n_matches = len(match_detail.tags_matched) + len(match_detail.albums_matched)
        if n_matches > 1:
            photo_url = (
                f"{IMMICH_WEB_BASE_URL}{IMMICH_PHOTO_PATH_TEMPLATE.format(id=self.id)}"
            )
            msg = f"[ERROR] Asset id={self.id} ({self.original_file_name}) is classified by more than one criterion: tags={match_detail.tags_matched}, albums={match_detail.albums_matched}\nLink: {photo_url}"
            if fail_fast:
                raise Exception(msg)
            else:
                print(msg)
            return True
        return False

    @typechecked
    def ensure_autotag_category_unknown(
        self,
        classified: bool,
        tag_mod_report: "TagModificationReport | None" = None,
        user: str | None = None,
    ) -> None:
        """
        Add or remove the AUTOTAG_UNKNOWN_CATEGORY tag according to classification state.
        If not classified, add the tag only if not present. If classified and tag is present, remove it.
        Idempotent: does nothing if already in correct state.
        """
        tag_name = AUTOTAG_CATEGORY_UNKNOWN
        if not classified:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name, tag_mod_report=tag_mod_report, user=user)
                print(
                    f"[WARN] asset.id={self.id} ({self.original_file_name}) is not classified. Tagged as '{tag_name}'."
                )
        else:
            if self.has_tag(tag_name):
                print(
                    f"[INFO] Removing tag '{tag_name}' from asset.id={self.id} because it is now classified."
                )
                self.remove_tag_by_name(
                    tag_name, tag_mod_report=tag_mod_report, user=user
                )

    @typechecked
    def ensure_autotag_conflict_category(
        self,
        conflict: bool,
        tag_mod_report: "TagModificationReport | None" = None,
        user: str | None = None,
    ) -> None:
        """
        Adds or removes the AUTOTAG_CONFLICT_CATEGORY tag according to conflict state.
        If there is conflict, adds the tag if not present. If no conflict and tag is present, removes it.
        """
        tag_name = AUTOTAG_CATEGORY_CONFLICT
        if conflict:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name, tag_mod_report=tag_mod_report, user=user)
                print(
                    f"[WARN] asset.id={self.id} ({self.original_file_name}) is in classification conflict. Tagged as '{tag_name}'."
                )
        else:
            if self.has_tag(tag_name):
                print(
                    f"[INFO] Removing tag '{tag_name}' from asset.id={self.id} because it's no longer in conflict."
                )
                self.remove_tag_by_name(
                    tag_name, tag_mod_report=tag_mod_report, user=user
                )

    @typechecked
    def apply_tag_conversions(
        self,
        tag_conversions: list,
        tag_mod_report: "TagModificationReport | None" = None,
    ):
        """
        For each tag conversion (origin -> destination), if the asset has the origin tag:
        - If it does not have the destination tag, add it and reload the asset, then remove the origin tag.
        - If it has both, just remove the origin tag.
        All actions are logged in tag_mod_report if provided.
        """
        from immich_client.api.assets import get_asset_info
        for conv in tag_conversions:
            origin = conv["origin"]
            dest = conv["destination"]
            has_origin = self.has_tag(origin)
            has_dest = self.has_tag(dest)
            if has_origin and not has_dest:
                try:
                    self.add_tag_by_name(dest, tag_mod_report=tag_mod_report)
                    # Reload asset to ensure state is up-to-date before removing origin
                    updated = get_asset_info.sync(
                        id=self.id, client=self.context.client
                    )
                    object.__setattr__(self, "asset", updated)
                except Exception as e:
                    print(f"[WARN] Could not add tag '{dest}' to asset {self.id}: {e}")
                self.remove_tag_by_name(origin, tag_mod_report=tag_mod_report)
            elif has_origin and has_dest:
                self.remove_tag_by_name(origin, tag_mod_report=tag_mod_report)

    @typechecked
    def try_detect_album_from_folders(self):
        """
        Attempts to detect a reasonable album name from the asset's folder path, according to the feature spec.
        Only runs if ENABLE_ALBUM_DETECTION_FROM_FOLDERS is True, the asset does not already belong to an album,
        and does not have a classified tag. Returns the detected album name or None. Raises NotImplementedError for ambiguous cases.
        Improved: If the date folder is the parent of the containing folder, concatenate both (date + subfolder) for the album name.
        If the date is already in the containing folder, keep as before.
        """
        import re

        if not ENABLE_ALBUM_DETECTION_FROM_FOLDERS:
            return None
        # If already classified by tag or album, skip
        if self.is_asset_classified():
            return None
        # If already in an album matching ALBUM_PATTERN, skip
        if any(re.match(ALBUM_PATTERN, name) for name in self.get_album_names()):
            return None
        analyzer = AlbumFolderAnalyzer(self.original_path)
        return analyzer.get_album_name()
