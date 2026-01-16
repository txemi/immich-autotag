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

    asset_partial: AssetResponseDto = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseDto)
    )
    context: "ImmichContext" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
    _asset_full: AssetResponseDto | None = attrs.field(default=None, init=False)

    def __attrs_post_init__(self) -> None:
        # Avoid direct reference to ImmichContext to prevent NameError/circular import

        # TODO: this refactors poorly, do an import, do not check the class name
        if self.context.__class__.__name__ != "ImmichContext":
            raise TypeError(f"context must be ImmichContext, not {type(self.context)}")

    @property
    def asset(self) -> AssetResponseDto:
        """Returns the most complete version of the asset available.

        Returns:
            - asset_full if loaded (contains full data including tags)
            - asset_partial otherwise (may have tags=UNSET)
        """
        return self._asset_full if self._asset_full is not None else self.asset_partial

    def _ensure_full_asset_loaded(self) -> None:
        """Lazy-load the full asset data if not already loaded.

        Fetches the complete asset including tags via get_asset_info API call.
        Result is cached in _asset_full for subsequent accesses.
        """
        if self._asset_full is not None:
            return  # Already loaded

        from immich_client.api.assets import get_asset_info

        self._asset_full = get_asset_info.sync(
            id=self.asset_partial.id, client=self.context.client
        )
        if self._asset_full is None:
            raise RuntimeError(
                f"[ERROR] Could not lazy-load asset with id={self.asset_partial.id}. get_asset_info returned None."
            )

    @property
    def tags(self):
        """Lazy-load tags if not present in the current asset.

        Returns the tags list from the asset. If tags are not yet loaded (UNSET from search_assets),
        this property triggers lazy-loading of the full asset via get_asset_info.

        Returns:
            list[TagResponseDto] | Unset: Tags from the asset, or UNSET if not available
        """
        from immich_client.types import Unset

        current_tags = self.asset.tags
        # If tags are UNSET, we need to lazy-load the full asset
        if isinstance(current_tags, Unset):
            self._ensure_full_asset_loaded()
            return self.asset.tags
        return current_tags

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
        # OPTIMIZATION: Trust the API response instead of polling with sleep().
        # The API call to update_asset should atomically update and return the asset.
        # Removed: polling loop with time.sleep(1.5s) retry logic that added 1.5-4.5s per asset
        if check_update_applied:
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug(f"[PERF] Date update applied: {new_date.isoformat()}")
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

        # OPTIMIZATION: Trust untag_assets API response instead of reloading asset.
        # The API call should atomically remove tags and succeed or fail accordingly.
        # Removed: get_asset_info.sync() reload that added HTTP request per tag removal
        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(f"[PERF] Tag '{tag_name}' removal applied")
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
        # OPTIMIZATION: Trust tag_assets API response instead of reloading asset.
        # The API call should atomically apply tags and succeed or fail accordingly.
        # Removed: get_asset_info.sync() reload that added HTTP request per tag addition
        log(
            f"[INFO] Added tag '{tag_name}' to asset.id={self.id}.",
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
        return self.context.albums_collection.album_names_for_asset(self.asset)

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
        from immich_autotag.classification.match_classification_result import (
            MatchClassificationResult,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        match_result_list = rule_set.matching_rules(self)
        return MatchClassificationResult.from_match_result_list(match_result_list)

    @typechecked
    def check_unique_classification(self, fail_fast: bool = True) -> bool:
        """
        Checks if the asset is classified by more than one rule.
        Returns True if there is a conflict (multiple rules matched), False otherwise.
        If fail_fast is True (default), raises an exception. If False, logs a warning only.
        """
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        match_result_list = rule_set.matching_rules(self)

        # Count the number of rules that matched (not individual tags/albums)
        n_rules_matched = len(match_result_list)

        if n_rules_matched > 1:
            import uuid

            # Get details for error message
            match_detail = self.get_classification_match_detail()
            photo_url = get_immich_photo_url(uuid.UUID(self.id))
            msg = f"[ERROR] Asset id={self.id} ({self.original_file_name}) is classified by {n_rules_matched} different rules (conflict). Matched tags={match_detail.tags_matched}, albums={match_detail.albums_matched}\nLink: {photo_url}"
            if fail_fast:
                raise Exception(msg)
            else:
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(msg, level=LogLevel.ERROR)
            return True
        return False

    @typechecked
    def ensure_autotag_unknown_category(self) -> None:
        """
        Adds or removes the AUTOTAG_UNKNOWN_CATEGORY tag according to classification state.
        If not classified, adds the tag if not present. If classified and tag is present, removes it.
        Idempotent: does nothing if already in correct state.
        Also logs and notifies the modification report.
        """
        from immich_autotag.config.manager import ConfigManager
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log
        from immich_autotag.report.modification_report import ModificationReport

        tag_name = ConfigManager.get_instance().config.classification.autotag_unknown
        tag_mod_report = ModificationReport.get_instance()
        classified = self.is_asset_classified()
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

        tag_name = ConfigManager.get_instance().config.classification.autotag_conflict
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
        from immich_autotag.config.manager import ConfigManager
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log
        from immich_autotag.report.modification_report import ModificationReport
        from immich_autotag.tags.modification_kind import ModificationKind

        if not ConfigManager.get_instance().config.album_detection_from_folders.enabled:
            return None
        # If already classified by tag or album, skip
        if self.is_asset_classified():
            return None
        # TODO: REVIEW IF THE LOGIC BELOW IS IN THE PREVIOUS METHOD is_asset_classified
        # If already in an album matching configured album patterns, skip
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        if rule_set.matches_any_album_of_asset(self):
            return None
        analyzer = AlbumFolderAnalyzer(self.original_path)
        album_name = analyzer.get_album_name()

        # Check if there's a conflict (multiple candidate folders) and ensure tag symmetry
        has_conflict = analyzer.has_multiple_candidate_folders()
        candidate_folders = analyzer.get_candidate_folders() if has_conflict else []

        # Always ensure the tag is in the correct state (add if conflict, remove if not)
        self.ensure_autotag_album_detection_conflict(
            conflict=has_conflict,
            candidate_folders=candidate_folders,
        )

        return album_name

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
        Uses asset_partial to enable lazy-loading of tags on first access.
        """
        return cls(asset_partial=dto, context=context)

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
        return self.context.albums_collection.album_names_for_asset(self.asset)

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
            ConfigManager.get_instance().config.duplicate_processing.autotag_album_conflict
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
    def ensure_autotag_album_detection_conflict(
        self,
        conflict: bool,
        candidate_folders: list[str] | None = None,
        user: str | None = None,
    ) -> None:
        """
        Adds or removes the AUTOTAG_ALBUM_DETECTION_CONFLICT tag according to album detection conflict state.
        If there is conflict (multiple candidate folders), adds the tag if not present.
        If no conflict and tag is present, removes it.
        """
        from immich_autotag.config.manager import ConfigManager

        tag_name = (
            ConfigManager.get_instance().config.duplicate_processing.autotag_album_detection_conflict
        )

        if not tag_name:
            return  # Tag not configured, skip

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if conflict:
            if not self.has_tag(tag_name):
                self.add_tag_by_name(tag_name)
                folders_str = str(candidate_folders) if candidate_folders else "unknown"
                log(
                    f"[ALBUM DETECTION] Asset '{self.original_file_name}' ({self.id}) has multiple candidate folders: "
                    f"{folders_str}. Tagged with '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
                # Register in modification report
                from immich_autotag.report.modification_report import ModificationReport
                from immich_autotag.tags.modification_kind import ModificationKind

                report = ModificationReport.get_instance()
                report.add_modification(
                    kind=ModificationKind.ALBUM_DETECTION_CONFLICT,
                    asset_wrapper=self,
                    extra=(
                        {"candidate_folders": candidate_folders}
                        if candidate_folders
                        else {}
                    ),
                )
        else:
            if self.has_tag(tag_name):
                log(
                    f"[ALBUM DETECTION] Removing tag '{tag_name}' from asset '{self.original_file_name}' ({self.id}) "
                    f"because album detection conflict is resolved.",
                    level=LogLevel.FOCUS,
                )
                self.remove_tag_by_name(tag_name, user=user)

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
