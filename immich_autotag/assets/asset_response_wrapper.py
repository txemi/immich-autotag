from __future__ import annotations

from datetime import datetime
from typing import List

from immich_autotag.conversions.conversion_wrapper import ConversionWrapper
from immich_autotag.conversions.tag_conversions import TagConversions
from immich_autotag.logging.levels import LogLevel
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper
from immich_autotag.users.user_response_wrapper import UserResponseWrapper


# Exception for date integrity
class DateIntegrityError(Exception):
    pass


from typing import TYPE_CHECKING
from urllib.parse import ParseResult
from uuid import UUID

import attrs
from immich_client.api.assets import get_asset_info
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.update_asset_dto import UpdateAssetDto
from typeguard import typechecked

from immich_autotag.albums.album_folder_analyzer import AlbumFolderAnalyzer
from immich_autotag.classification.match_classification_result import (
    MatchClassificationResult,
)
from immich_autotag.config.manager import ConfigManager
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.utils.get_immich_album_url import get_immich_photo_url

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True)
class AssetResponseWrapper:

    asset: AssetResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseDto)
    )
    context: "ImmichContext" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )

    def __attrs_post_init__(self) -> None:
        # Avoid direct reference to ImmichContext to prevent NameError/circular import

        # TODO: this refactors poorly, do an import, do not check the class name
        if self.context.__class__.__name__ != "ImmichContext":
            raise TypeError(f"context must be ImmichContext, not {type(self.context)}")

    @typechecked
    def update_date(
        self,
        new_date: datetime,
        check_update_applied: bool = False,
    ) -> None:
        """
        Updates the main date (created_at) of the asset using the Immich API.
        If tag_mod_report is provided, logs the modification.
        """
        import pytz
        from immich_client.api.assets import update_asset
        from immich_client.models.update_asset_dto import UpdateAssetDto

        old_date = self.asset.created_at
        # Ensure the date is timezone-aware in UTC
        if new_date.tzinfo is None:
            raise ValueError(
                "[ERROR] new_date must be timezone-aware. Received naive datetime. Asset will not be updated."
            )
        dto = UpdateAssetDto(date_time_original=new_date.isoformat())
        # Log and print before updating the asset, including link to the photo in Immich
        from immich_autotag.logging.utils import is_log_level_enabled, log_debug

        if is_log_level_enabled(LogLevel.DEBUG):
            photo_url_obj = self.get_immich_photo_url()
            photo_url = photo_url_obj.geturl()
            log_msg = (
                f"[INFO] Updating asset date: asset.id={self.id}, asset_name={self.original_file_name}, "
                f"old_date={old_date}, new_date={new_date}\n[INFO] Immich photo link: {photo_url}"
            )
            log_debug(f"[BUG] {log_msg}")
        from immich_autotag.report.modification_report import ModificationReport
        from immich_autotag.tags.modification_kind import ModificationKind
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper

        tag_mod_report = ModificationReport.get_instance()
        user_wrapper = UserResponseWrapper.from_context(self.context)
        asset_url = self.get_immich_photo_url().geturl()

        tag_mod_report.add_modification(
            kind=ModificationKind.UPDATE_ASSET_DATE,
            asset_wrapper=self,
            old_value=str(old_date) if old_date else None,
            new_value=str(new_date) if new_date else None,
            user=user_wrapper,
            extra={"pre_update": True},
        )
        response = update_asset.sync(id=self.id, client=self.context.client, body=dto)
        # Fail-fast: check response type and status directly, no dynamic attribute access
        # If the API returns a response object with status_code, check it; otherwise, assume success if no exception was raised
        # If the response is an AssetResponseDto, we expect no error field and no status_code
        # If the API changes and returns a dict or error object, this will fail fast
        if not isinstance(response, AssetResponseDto):
            raise DateIntegrityError(
                f"[ERROR] update_asset.sync did not return AssetResponseDto, got {type(response)}: {response} for asset.id={self.id} ({self.original_file_name})"
            )
        # If the response has an 'error' attribute and it is not None, fail fast (static access only)
        # This assumes that if present, 'error' is a public attribute of the response object
        import time

        from immich_client.api.assets import get_asset_info

        if check_update_applied:
            max_retries = 3
            retry_delay = 1.5  # seconds
            for attempt in range(max_retries):
                updated_asset = get_asset_info.sync(
                    id=self.id, client=self.context.client
                )
                updated_created_at = updated_asset.created_at
                if (
                    updated_created_at is not None
                    and updated_created_at.isoformat() == new_date.isoformat()
                ):
                    self.asset = updated_asset
                    return
                if attempt < max_retries - 1:
                    if is_log_level_enabled(LogLevel.DEBUG):
                        log_debug(
                            f"[BUG][WARN] Date not updated yet after update (attempt {attempt+1}/{max_retries}), waiting {retry_delay}s..."
                        )
                    time.sleep(retry_delay)
            # If after retries it is still not updated, print all dates and warning
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug("[BUG][AFTER UPDATE] Dates of the updated asset:")
                log_debug(
                    f"[BUG]   created_at:      {getattr(updated_asset, 'created_at', None)}"
                )
                log_debug(
                    f"[BUG]   file_created_at: {getattr(updated_asset, 'file_created_at', None)}"
                )
                log_debug(
                    f"[BUG]   exif_created_at: {getattr(updated_asset, 'exif_created_at', None)}"
                )
                log_debug(
                    f"[BUG]   updated_at:      {getattr(updated_asset, 'updated_at', None)}"
                )
                log_debug(
                    f"[BUG][WARNING] Asset date update failed: expected {new_date.isoformat()}, got {updated_created_at.isoformat() if updated_created_at else None} for asset.id={self.id} ({self.original_file_name})"
                )
            self.asset = updated_asset
            return

    @typechecked
    def get_immich_photo_url(self) -> ParseResult:
        """
        Returns the Immich web URL for this asset as a string.
        """
        from immich_autotag.utils.url_helpers import get_immich_photo_url

        return get_immich_photo_url(self.uuid)

    @typechecked
    def get_best_date(self) -> datetime:
        """
        Returns the best possible date for the asset, using only DTO fields:
        - created_at
        - file_created_at
        - exif_created_at
        Chooses the oldest and raises an exception if any is earlier than the chosen one.
        """
        date_candidates: List[datetime] = []
        # Only DTO dates
        for attr in ("created_at", "file_created_at", "exif_created_at"):
            dt = getattr(self.asset, attr, None)
            if dt is not None:
                if not isinstance(dt, datetime):
                    raise TypeError(f"{attr} is not datetime: {dt!r}")
                date_candidates.append(dt)
        if not date_candidates:
            raise ValueError("Could not determine any date for the asset.")
        best_date = min(date_candidates)
        for d in date_candidates:
            if d < best_date:
                raise DateIntegrityError(
                    f"Integrity broken: found a date ({d}) earlier than the best selected date ({best_date}) for asset {self.asset.id}"
                )
        return best_date

    @typechecked
    def get_all_duplicate_wrappers(
        self, include_self: bool = True
    ) -> list["AssetResponseWrapper"]:
        """
        Returns a list of AssetResponseWrapper objects for all duplicates of this asset.
        If include_self is True, includes this asset as well.
        """
        from uuid import UUID

        context = self.context
        duplicate_id = self.duplicate_id_as_uuid
        wrappers = []
        if duplicate_id is not None:
            group = context.duplicates_collection.get_group(duplicate_id)
            for dup_id in group:
                if not include_self and str(dup_id) == self.asset.id:
                    continue
                dup_asset = context.asset_manager.get_asset(dup_id, context)
                if dup_asset is not None:
                    wrappers.append(dup_asset)
        if include_self and (self not in wrappers):
            wrappers.append(self)
        return wrappers

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
        user: "UserResponseWrapper | None" = None,
        fail_on_error: bool = False,
    ) -> bool:
        """
        Removes all tags from the asset with the given name (case-insensitive), even if they have different IDs (e.g., global and nested tags).
        Returns True if at least one was removed, False if none were found.
        After removal, reloads the asset and checks if the tag is still present. Raises if any remain.
        Uses TagWrapper from the tag collection for all reporting.
        """
        from immich_client.api.assets import get_asset_info
        from immich_client.api.tags import untag_assets
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        from immich_autotag.logging.utils import is_log_level_enabled, log_debug

        # Find all tag objects on the asset with the given name (case-insensitive)
        tags_to_remove = [
            tag for tag in self.asset.tags if tag.name.lower() == tag_name.lower()
        ]

        if tags_to_remove:
            # Use the TagWrapper for statistics, not the string
            tag_wrapper = self.context.tag_collection.find_by_name(tag_name)
        if not tags_to_remove:
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug(
                    f"[BUG][INFO] Asset id={self.id} does not have the tag '{tag_name}'"
                )
            return False

        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(
                f"[BUG] Before removal: asset.id={self.id}, asset_name={self.original_file_name}, tag_name='{tag_name}', tag_ids={[tag.id for tag in tags_to_remove]}"
            )
            log_debug(f"[BUG] Tags before removal: {self.get_tag_names()}")

        # Get the TagWrapper from the tag collection for reporting, robust and explicit
        assert isinstance(
            self.context.tag_collection, TagCollectionWrapper
        ), "context.tag_collection must be an object"
        tag_wrapper = self.context.tag_collection.find_by_name(tag_name)

        removed_any = False
        from immich_autotag.report.modification_report import ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        for tag in tags_to_remove:
            response = untag_assets.sync(
                id=tag.id, client=self.context.client, body=BulkIdsDto(ids=[self.id])
            )
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug(
                    f"[BUG] Full untag_assets response for tag_id={tag.id}: {response}"
                )
                log_debug(
                    f"[BUG][INFO] Removed tag '{tag_name}' (id={tag.id}) from asset.id={self.id}. Response: {response}"
                )
            removed_any = True
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report.add_modification(
                kind=ModificationKind.REMOVE_TAG_FROM_ASSET,
                asset_wrapper=self,
                tag=tag_wrapper,
                user=user,
            )

        # Reload asset and check if tag is still present
        updated_asset = get_asset_info.sync(id=self.id, client=self.context.client)
        self.asset = updated_asset
        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(f"[BUG] Tags after removal: {self.get_tag_names()}")
        tag_still_present = self.has_tag(tag_name)
        if tag_still_present:
            error_msg = f"[ERROR] Tag '{tag_name}' could NOT be removed from asset.id={self.id} ({self.original_file_name}). Still present after API call."
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report.add_modification(
                kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                asset_wrapper=self,
                tag=tag_wrapper,
                user=user,
                extra={"error": error_msg},
            )
            from immich_autotag.logging.utils import log

            log(error_msg, level=LogLevel.IMPORTANT)
            if fail_on_error:
                raise RuntimeError(error_msg)
            # else: just log and continue
        return removed_any

    @typechecked
    def add_tag_by_name(
        self,
        tag_name: str,
        fail_if_exists: bool = False,
    ) -> bool:
        """
        Adds a tag to the asset by name using the Immich API if it doesn't have it already.
        Returns True if added, raises exception if it already had it or if the tag doesn't exist.
        """
        from immich_client.api.tags import tag_assets
        from immich_client.models.bulk_ids_dto import BulkIdsDto

        from immich_autotag.report.modification_report import ModificationReport
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper

        tag_mod_report = ModificationReport.get_instance()

        # Get the UserWrapper in a clean and encapsulated way
        user_wrapper = UserResponseWrapper.from_context(self.context)

        tag = self.context.tag_collection.find_by_name(tag_name)
        if tag is None:
            tag = self.context.tag_collection.create_tag_if_not_exists(
                tag_name, self.context.client
            )
        # Check if the asset already has the tag
        if self.has_tag(tag_name):
            if fail_if_exists:
                raise ValueError(
                    f"[INFO] Asset.id={self.id} already has tag '{tag_name}'"
                )
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(
                f"[INFO] Asset.id={self.id} already has tag '{tag_name}', skipping.",
                level=LogLevel.DEBUG,
            )
            return False
        # Extra checks and logging before API call
        if not tag or tag.id is None:
            error_msg = f"[ERROR] Tag object for '{tag_name}' is missing or has no id. Tag: {tag}"
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(error_msg, level=LogLevel.ERROR)
            from immich_autotag.tags.modification_kind import ModificationKind

            tag_mod_report.add_modification(
                kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                asset_wrapper=self,
                tag=tag,
                user=user_wrapper,
                extra={"error": error_msg},
            )
            return False
        if not self.id:
            error_msg = f"[ERROR] Asset object is missing id. Asset: {self.asset}"
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(error_msg, level=LogLevel.ERROR)
            if tag_mod_report:
                from immich_autotag.tags.modification_kind import ModificationKind

                tag_mod_report.add_modification(
                    asset_id=None,
                    asset_name=self.original_file_name,
                    kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                    tag=tag,
                    user=user_wrapper,
                    extra={"error": error_msg},
                )
            return False
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            f"[DEBUG] Calling tag_assets.sync with tag_id={tag.id} and asset_id={self.id}",
            level=LogLevel.DEBUG,
        )

        # Statistics update is handled by modification_report, not directly here
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        try:
            response = tag_assets.sync(
                id=tag.id, client=self.context.client, body=BulkIdsDto(ids=[self.id])
            )
        except Exception as e:
            error_msg = f"[ERROR] Exception during tag_assets.sync: {e}"
            log(error_msg, level=LogLevel.ERROR)
            if tag_mod_report:
                from immich_autotag.tags.modification_kind import ModificationKind

                tag_mod_report.add_modification(
                    asset_wrapper=self,
                    kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                    tag=tag,
                    user=user_wrapper,
                    extra={"error": error_msg},
                )
            return False
        log(f"[DEBUG] Response tag_assets: {response}", level=LogLevel.DEBUG)
        # Request the asset again and check if the tag is applied
        updated_asset = get_asset_info.sync(id=self.id, client=self.context.client)
        log(f"[DEBUG] Asset after tag_assets: {updated_asset}", level=LogLevel.DEBUG)
        tag_names = (
            [tag.name for tag in updated_asset.tags] if updated_asset.tags else []
        )
        if tag_name not in tag_names:
            error_msg = f"[ERROR] Tag '{tag_name}' doesn't appear in the asset after update. Current tags: {tag_names}"
            log(error_msg, level=LogLevel.ERROR)
            if tag_mod_report:
                from immich_autotag.tags.modification_kind import ModificationKind

                tag_mod_report.add_modification(
                    asset_wrapper=self,
                    kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                    tag=tag,
                    user=user_wrapper,
                    extra={"error": error_msg},
                )
            return False
        log(
            f"[INFO] Added tag '{tag_name}' to asset.id={self.id}. Current tags: {tag_names}",
            level=LogLevel.DEBUG,
        )
        from immich_autotag.tags.modification_kind import ModificationKind

        tag_mod_report.add_modification(
            kind=ModificationKind.ADD_TAG_TO_ASSET,
            asset_wrapper=self,
            tag=tag,
            user=user_wrapper,
        )
        return True

    @typechecked
    def _get_current_tag_ids(self) -> list[str]:
        """Returns the IDs of the asset's current tags."""
        if self.asset.tags is None:
            return []
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
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        # If any rule matches, asset is classified
        return bool(rule_set.matching_rules(self))

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
    def original_path(self) -> "Path":
        from pathlib import Path

        path = Path(self.asset.original_path)

        return path

    @property
    def duplicate_id_as_uuid(self) -> "UUID | None":
        """
        Returns the duplicate_id as UUID (or None if not present or invalid).
        """
        from uuid import UUID

        val = self.asset.duplicate_id
        if val is None:
            return None
        try:
            return UUID(val)
        except Exception:
            return None

    @typechecked
    def get_classification_match_detail(self) -> MatchClassificationResult:
        """
        Returns an object with the detail of the tags and albums that matched classification.
        """
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        match_results = rule_set.matching_rules(self)
        tags_matched = [m.tag_name for m in match_results if m.tag_name is not None]
        albums_matched = [
            m.album_name for m in match_results if m.album_name is not None
        ]
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
            import uuid

            photo_url = get_immich_photo_url(uuid.UUID(self.id))
            msg = f"[ERROR] Asset id={self.id} ({self.original_file_name}) is classified by more than one criterion: tags={match_detail.tags_matched}, albums={match_detail.albums_matched}\nLink: {photo_url}"
            if fail_fast:
                raise Exception(msg)
            else:
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(msg, level=LogLevel.ERROR)
            return True
        return False

    @typechecked
    def ensure_autotag_category_unknown(
        self,
        classified: bool,
    ) -> None:
        """
        Add or remove the AUTOTAG_UNKNOWN_CATEGORY tag according to classification state.
        If not classified, add the tag only if not present. If classified and tag is present, remove it.
        Idempotent: does nothing if already in correct state.
        """
        from immich_autotag.config.manager import (
            ConfigManager,
        )
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        tag_name = ConfigManager.get_instance().config.auto_tags.category_unknown
        from immich_autotag.report.modification_report import ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        if not classified:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name)
                log(
                    f"[CLASSIFICATION] asset.id={self.id} ({self.original_file_name}) is not classified. Tagged as '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.id} ({self.original_file_name}) is not classified. Tag '{tag_name}' already present.",
                    level=LogLevel.FOCUS,
                )
        else:
            if self.has_tag(tag_name):
                log(
                    f"[CLASSIFICATION] Removing tag '{tag_name}' from asset.id={self.id} ({self.original_file_name}) because it is now classified.",
                    level=LogLevel.FOCUS,
                )
                self.remove_tag_by_name(tag_name)
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.id} ({self.original_file_name}) is classified. Tag '{tag_name}' not present.",
                    level=LogLevel.FOCUS,
                )

    @typechecked
    def ensure_autotag_conflict_category(
        self,
        conflict: bool,
        user: UserResponseWrapper | None = None,
    ) -> None:
        """
        Adds or removes the AUTOTAG_CONFLICT_CATEGORY tag according to conflict state.
        If there is conflict, adds the tag if not present. If no conflict and tag is present, removes it.
        """
        from immich_autotag.config.manager import (
            ConfigManager,
        )
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        tag_name = ConfigManager.get_instance().config.auto_tags.category_conflict
        from immich_autotag.report.modification_report import ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        if conflict:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name)
                log(
                    f"[CLASSIFICATION] asset.id={self.id} ({self.original_file_name}) is in classification conflict. Tagged as '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.id} ({self.original_file_name}) is in classification conflict. Tag '{tag_name}' already present.",
                    level=LogLevel.FOCUS,
                )
        else:
            if self.has_tag(tag_name):
                log(
                    f"[CLASSIFICATION] Removing tag '{tag_name}' from asset.id={self.id} ({self.original_file_name}) because it's no longer in conflict.",
                    level=LogLevel.FOCUS,
                )
                # If user is None, get the wrapper from the context
                if user is None:
                    user = UserResponseWrapper.from_context(self.context)
                self.remove_tag_by_name(tag_name, user=user)
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.id} ({self.original_file_name}) is not in conflict. Tag '{tag_name}' not present.",
                    level=LogLevel.FOCUS,
                )

    @typechecked
    def apply_tag_conversions(
        self,
        tag_conversions: TagConversions,
    ) -> None:
        """
        For each tag conversion (origin -> destination), if the asset has the origin tag:
        - If it does not have the destination tag, add it and reload the asset, then remove the origin tag.
        - If it has both, just remove the origin tag.
        In focus mode, logs if a tag was added, removed, or nothing was done.
        """
        from immich_client.api.assets import get_asset_info

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        changes = []

        for conv in tag_conversions:
            assert isinstance(
                conv, ConversionWrapper
            ), f"Tag conversion must be a ConversionWrapper, got {type(conv)}"
            origin = conv.get_single_origin_tag()
            dest_tags = conv.destination_tags()
            if len(dest_tags) != 1:
                raise NotImplementedError(
                    "Only single destination tag conversions are implemented."
                )
            dest = dest_tags[0]
            has_origin = self.has_tag(origin)
            has_dest = self.has_tag(dest)
            if has_origin and not has_dest:
                try:
                    self.add_tag_by_name(dest)
                    # Reload asset to ensure state is up-to-date before removing origin
                    updated = get_asset_info.sync(
                        id=self.id, client=self.context.client
                    )
                    object.__setattr__(self, "asset", updated)
                    changes.append(f"Added tag '{dest}' and removed '{origin}'")
                except Exception as e:
                    msg = f"[WARN] Could not add tag '{dest}' to asset {self.id}: {e}"
                    print(msg)
                    changes.append(f"Failed to add '{dest}', removed '{origin}'")
                self.remove_tag_by_name(origin)
            elif has_origin and has_dest:
                self.remove_tag_by_name(origin)
                changes.append(
                    f"Removed redundant tag '{origin}' (already had '{dest}')"
                )
        if changes:
            for c in changes:
                log(
                    f"[TAG CONVERSION] {c} on asset {self.id} ({self.original_file_name})",
                    level=LogLevel.FOCUS,
                )
        else:
            log(
                f"[TAG CONVERSION] No tag changes performed on asset {self.id} ({self.original_file_name})",
                level=LogLevel.FOCUS,
            )
        log(
            f"[TAG CONVERSION] Tag conversion finished for asset {self.id} ({self.original_file_name})",
            level=LogLevel.FOCUS,
        )

    @typechecked
    def try_detect_album_from_folders(self) -> str | None:
        """
        Attempts to detect a reasonable album name from the asset's folder path, according to the feature spec.
        Only runs if enable_album_detection_from_folders (from config) is True, the asset does not already belong to an album,
        and does not have a classified tag. Returns the detected album name or None. Raises NotImplementedError for ambiguous cases.
        Improved: If the date folder is the parent of the containing folder, concatenate both (date + subfolder) for the album name.
        If the date is already in the containing folder, keep as before.
        """
        import re

        if (
            not ConfigManager.get_instance().config.features.album_detection_from_folders.enabled
        ):
            return None
        # If already classified by tag or album, skip
        if self.is_asset_classified():
            return None
        # TODO: REVIEW IF THE LOGIC BELOW IS IN THE PREVIOUS METHOD is_asset_classified
        # If already in an album matching configured album patterns, skip
        from immich_autotag.classification.classification_rule_set import ClassificationRuleSet
        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        if rule_set.matches_any_album_of_asset(self):
            return None
        analyzer = AlbumFolderAnalyzer(self.original_path)
        return analyzer.get_album_name()

    @property
    def id_as_uuid(self) -> "UUID":
        from uuid import UUID

        return UUID(self.asset.id)

    @classmethod
    def from_dto(
        cls: type["AssetResponseWrapper"],
        dto: AssetResponseDto,
        context: "ImmichContext",
    ) -> "AssetResponseWrapper":
        """
        Creates an AssetResponseWrapper from a DTO and a context.
        """
        return cls(asset=dto, context=context)

    @typechecked
    def has_same_classification_tags_as(self, other: "AssetResponseWrapper") -> bool:
        """
        Compare classification tags between self and another AssetResponseWrapper.
        Returns True if tags are equal, False otherwise.
        """
        return set(self.get_classification_tags()) == set(
            other.get_classification_tags()
        )

    @typechecked
    def get_classification_tags(self) -> list[str]:
        """
        Returns the classification tags for this asset, using the ClassificationRuleSet from config manager.
        Only tags configured as relevant for classification in the config are considered.
        """
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        match_results = rule_set.matching_rules(self)
        return match_results.tags()

    @typechecked
    def get_link(self) -> ParseResult:
        """
        Returns a ParseResult URL object for this asset.
        """
        from urllib.parse import ParseResult, urlparse

        from immich_autotag.utils.url_helpers import get_immich_photo_url

        url = get_immich_photo_url(self.uuid)
        return url

    @property
    def uuid(self) -> UUID:
        return UUID(self.asset.id)

    def get_album_names(self) -> list[str]:
        """
        Returns the names of the albums this asset belongs to.
        """
        return self.context.albums_collection.albums_for_asset(self.asset)

    @typechecked
    def get_duplicate_wrappers(self) -> list["AssetResponseWrapper"]:
        """
        Returns a list of AssetResponseWrapper objects for all duplicates of this asset (excluding itself).
        """
        from uuid import UUID

        context = self.context
        duplicate_id = self.duplicate_id_as_uuid
        wrappers = []
        if duplicate_id is not None:
            group = context.duplicates_collection.get_group(duplicate_id)
            for dup_id in group:
                if str(dup_id) == self.asset.id:
                    continue
                dup_asset = context.asset_manager.get_asset(dup_id, context)
                if dup_asset is not None:
                    wrappers.append(dup_asset)
        return wrappers

    @typechecked
    def ensure_autotag_duplicate_album_conflict(
        self,
        conflict: bool,
        # tag_mod_report parameter removed
        user: str | None = None,
        duplicate_id: str | None = None,
    ) -> None:
        """
        Adds or removes the AUTOTAG_DUPLICATE_ALBUM_CONFLICT tag according to duplicate album conflict state.
        If there is conflict, adds the tag if not present. If no conflict and tag is present, removes it.
        Also handles the per-duplicate-set tag if duplicate_id is provided.
        """
        from immich_autotag.config.manager import (
            ConfigManager,
        )

        tag_name = (
            ConfigManager.get_instance().config.auto_tags.duplicate_asset_album_conflict
        )
        # Generic tag
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if conflict:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name)
                log(
                    f"asset.id={self.id} ({self.original_file_name}) is in duplicate album conflict. Tagged as '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
        else:
            if self.has_tag(tag_name):
                log(
                    f"Removing tag '{tag_name}' from asset.id={self.id} because duplicate album conflict is resolved.",
                    level=LogLevel.FOCUS,
                )
                self.remove_tag_by_name(tag_name, user=user)
        # Per-duplicate-set tag
        if duplicate_id:
            tag_for_set = f"{tag_name}_{duplicate_id}"
            if conflict:
                if not self.has_tag(tag_for_set):
                    self.add_tag_by_name(tag_for_set)
                    log(
                        f"asset.id={self.id} ({self.original_file_name}) is in duplicate album conflict (set {duplicate_id}). Tagged as '{tag_for_set}'.",
                        level=LogLevel.FOCUS,
                    )
            else:
                if self.has_tag(tag_for_set):
                    log(
                        f"Removing tag '{tag_for_set}' from asset.id={self.id} because duplicate album conflict (set {duplicate_id}) is resolved.",
                        level=LogLevel.FOCUS,
                    )
                    self.remove_tag_by_name(tag_for_set, user=user)

    @typechecked
    def format_info(self) -> str:
        lines = [f"Asset {self.id} | {self.original_file_name}"]
        try:
            link = self.get_immich_photo_url().geturl()
        except Exception:
            link = "(no link)"
        lines.append(f"  Link: {link}")
        lines.append(f"  created_at: {getattr(self.asset, 'created_at', None)}")
        lines.append(
            f"  file_created_at: {getattr(self.asset, 'file_created_at', None)}"
        )
        lines.append(
            f"  exif_created_at: {getattr(self.asset, 'exif_created_at', None)}"
        )
        lines.append(f"  updated_at: {getattr(self.asset, 'updated_at', None)}")
        lines.append(f"  Tags: {self.get_tag_names()}")
        lines.append(f"  Albums: {self.get_album_names()}")
        lines.append(f"  Path: {getattr(self.asset, 'original_path', None)}")
        return "\n".join(lines)
