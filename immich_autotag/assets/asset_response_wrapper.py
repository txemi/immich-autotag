from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable
from urllib.parse import ParseResult

import attrs
from typeguard import typechecked

from immich_autotag.albums.folder_analysis.album_folder_analyzer import (
    AlbumFolderAnalyzer,
)
from immich_autotag.api.logging_proxy.types import Unset, UpdateAssetDto
from immich_autotag.assets.asset_cache_entry import (
    AssetCacheEntry,
)
from immich_autotag.classification.classification_status import ClassificationStatus
from immich_autotag.classification.match_classification_result import (
    MatchClassificationResult,
)
from immich_autotag.classification.match_result_list import MatchResultList
from immich_autotag.config.manager import ConfigManager
from immich_autotag.config.models import UserConfig
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.conversions.tag_conversions import TagConversions
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper
from immich_autotag.tags.tag_response_wrapper import TagWrapper
from immich_autotag.types.uuid_wrappers import AssetUUID, DuplicateUUID, TagUUID
from immich_autotag.users.user_response_wrapper import UserResponseWrapper
from immich_autotag.utils.url_helpers import get_immich_photo_url

if TYPE_CHECKING:
    from immich_autotag.assets.classification_validation_result import (
        ClassificationValidationResult,
    )


# Exception for date integrity
class DateIntegrityError(Exception):
    pass


@attrs.define(auto_attribs=True, slots=True)
class AssetResponseWrapper:

    _context: "ImmichContext" = attrs.field(
        validator=attrs.validators.instance_of(ImmichContext)
    )
    _cache_entry: AssetCacheEntry = attrs.field()

    # The rest of the methods will use self._cache_entry.get_state() instead of self._state directly.

    def __attrs_post_init__(self) -> None:
        # Use isinstance for type validation, which is more robust and preferred
        # ImmichContext type is enforced by attrs and type hints; no runtime check needed
        pass

    def get_context(self) -> "ImmichContext":
        """Read-only access to the context. No external modification allowed."""
        return self._context

    # Construction methods moved to AssetCacheEntry

    def get_tags(self) -> list[TagWrapper]:
        """Lazy-load tags if not present in the current asset.

        Returns the tags list from the asset. If tags are not yet loaded
        (UNSET from search_assets),
        this property triggers lazy-loading of the full asset via get_asset_info.

        Returns:
            list[TagWrapper]: Tag wrappers from the asset
        """

        # Use the public getter from AssetDtoState
        return self._cache_entry.get_tags()

    @typechecked
    def update_date(
        self,
        *,
        new_date: datetime,
        check_update_applied: bool = False,
    ) -> None:
        """
        Updates the main date (created_at) of the asset using the Immich API.
        If tag_mod_report is provided, logs the modification.
        """
        from immich_autotag.api.logging_proxy.logging_update_asset_date import (
            logging_update_asset_date,
        )

        old_date = self.get_created_at()
        if new_date.tzinfo is None:
            raise ValueError(
                (
                    "[ERROR] new_date must be timezone-aware. "
                    "Received naive datetime. Asset will not be updated."
                )
            )
        dto = UpdateAssetDto(date_time_original=new_date.isoformat())
        response = logging_update_asset_date(
            asset_wrapper=self,
            new_date=new_date,
            old_date=old_date,
            dto=dto,
            check_update_applied=check_update_applied,
        )

    @typechecked
    def get_immich_photo_url(self) -> ParseResult:
        """
        Returns the Immich web URL for this asset as a string.
        """
        from immich_autotag.utils.url_helpers import get_immich_photo_url

        return get_immich_photo_url(self.get_id())

    @typechecked
    def get_best_date(self) -> datetime:
        """
        Returns the best possible date for the asset, using all available DTO fields:
        - created_at
        - file_created_at
        - file_modified_at
        - local_date_time
        Chooses the oldest and raises an exception if any is earlier than the chosen one.
        """

        date_candidates = self._cache_entry.get_dates()
        if not date_candidates:
            raise ValueError("Could not determine any date for the asset.")
        best_date = min(date_candidates)
        for d in date_candidates:
            if d < best_date:
                raise DateIntegrityError(
                    (
                        f"Integrity broken: found a date ({d}) earlier than the best selected date "
                        f"({best_date}) for asset {self._cache_entry.get_uuid()}"
                    )
                )
        return best_date

    @typechecked
    def get_all_duplicate_wrappers(
        self, *, include_self: bool = True
    ) -> list["AssetResponseWrapper"]:
        """
        Returns a list of AssetResponseWrapper objects for all duplicates of this asset.
        If include_self is True, includes this asset as well.
        """

        context = self.get_context()
        duplicate_id = self.get_duplicate_id_as_uuid()
        wrappers: list[AssetResponseWrapper] = []
        if duplicate_id:
            group = context.get_duplicates_collection().get_group(duplicate_id)
            for dup_id in group:
                if (
                    not include_self
                    and dup_id == self._cache_entry.get_state().get_uuid()
                ):
                    continue
                dup_asset = context.get_asset_manager().get_asset(dup_id, context)
                if dup_asset is not None:
                    wrappers.append(dup_asset)
        if include_self and (self not in wrappers):
            wrappers.append(self)
        return wrappers

    @typechecked
    def has_tag(self, *, tag_name: str) -> bool:
        """
        Returns True if the asset has the tag with that name (case-insensitive).
        """
        return self._cache_entry.has_tag(tag_name)

    @typechecked
    def remove_tag_by_name(
        self,
        *,
        tag_name: str,
        user: "UserResponseWrapper | None" = None,
    ) -> ModificationEntriesList:
        """
        Removes all tags from the asset with the given name (case-insensitive),
        even if they have different IDs (e.g., global and nested tags).
        Returns a ModificationEntriesList with the recorded modifications.
        After removal, reloads the asset and checks if the tag is still present.
        Raises if any remain.
        Uses TagWrapper from the tag collection for all reporting.
        """

        from immich_autotag.logging.utils import is_log_level_enabled, log_debug

        tags = self.get_tags()
        tags_to_remove = [
            tag for tag in tags if tag.get_name().lower() == tag_name.lower()
        ]
        if not tags_to_remove:
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug(
                    f"[BUG][INFO] Asset id={self.get_id()} does not have the tag "
                    f"'{tag_name}'"
                )
            return ModificationEntriesList()

        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(
                f"[BUG] Before removal: asset.id={self.get_id()}, "
                f"asset_name={self.get_original_file_name()}, "
                f"tag_name='{tag_name}', "
                f"tag_ids={[str(tag.get_id()) for tag in tags_to_remove]}"
            )
            log_debug(f"[BUG] Tags before removal: {self.get_tag_names()}")

        assert isinstance(
            self.get_context().get_tag_collection(), TagCollectionWrapper
        ), "context.tag_collection must be an object"

        tag_wrapper = self.get_context().get_tag_collection().find_by_name(tag_name)
        if not tag_wrapper:
            error_msg = f"Tag '{tag_name}' not found in tag collection"
            log(error_msg, level=LogLevel.ERROR)
            return ModificationEntriesList()

        # Use logging_proxy for automatic error handling and reporting
        from immich_autotag.api.logging_proxy.logging_untag_assets import (
            logging_untag_assets_safe,
        )

        entries = logging_untag_assets_safe(
            client=self.get_context().get_client_wrapper().get_client(),
            tag=tag_wrapper,
            asset_wrappers=[self],
        )

        # Check if entries were created (success)
        if entries and is_log_level_enabled(LogLevel.DEBUG):
            log_debug(f"[PERF] Tag '{tag_name}' removal applied")

        return entries

    @typechecked
    def add_tag_by_name(
        self,
        *,
        tag_name: str,
        fail_if_exists: bool = False,
    ) -> ModificationEntriesList:
        """
        Adds a tag to the asset by name using the Immich API if it doesn\'t have it already.
        Returns a ModificationEntriesList with the recorded modifications.
        """
        from immich_autotag.api.immich_proxy.tags import proxy_tag_assets
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper

        tag_mod_report = ModificationReport.get_instance()

        # Get the UserWrapper in a clean and encapsulated way
        user_wrapper = UserResponseWrapper.load_current_user()

        tag = self.get_context().get_tag_collection().find_by_name(tag_name)
        if tag is None:
            tag = (
                self.get_context()
                .get_tag_collection()
                .create_tag_if_not_exists(
                    name=tag_name,
                    client=self.get_context().get_client_wrapper().get_client(),
                )
            )
        # Check if the asset already has the tag
        if self.has_tag(tag_name=tag_name):
            if fail_if_exists:
                raise ValueError(
                    f"[INFO] Asset.id={self.get_id()} already has tag '{tag_name}'"
                )
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(
                f"[INFO] Asset.id={self.get_id()} already has tag '{tag_name}', skipping.",
                level=LogLevel.DEBUG,
            )
            return ModificationEntriesList()
        # Extra checks and logging before API call
        if not tag:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            error_msg = f"[ERROR] Tag '{tag_name}' not found and could not be created."
            log(error_msg, level=LogLevel.ERROR)
            from immich_autotag.report.modification_kind import ModificationKind

            entry = tag_mod_report.add_modification(
                kind=ModificationKind.WARNING_TAG_ADDITION_TO_ASSET_FAILED,
                asset_wrapper=self,
                tag=tag,
                user=user_wrapper,
                extra={"error": error_msg},
            )
            return ModificationEntriesList(entries=[entry])
        if not self.get_id():
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            error_msg = f"[ERROR] Asset object is missing id. Asset state: {str(self._cache_entry.get_state())}"
            log(error_msg, level=LogLevel.ERROR)
            from immich_autotag.report.modification_kind import ModificationKind

            entry = tag_mod_report.add_modification(
                kind=ModificationKind.WARNING_TAG_ADDITION_TO_ASSET_FAILED,
                asset_wrapper=self,
                tag=tag,
                user=user_wrapper,
                extra={"error": error_msg},
            )
            return ModificationEntriesList(entries=[entry])
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            f"[DEBUG] Calling tag_assets.sync with tag_id={tag.get_id()} and asset_id={self.get_id()}",
            level=LogLevel.DEBUG,
        )

        # Statistics update is handled by modification_report, not directly here
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        try:
            response = proxy_tag_assets(
                tag_id=tag.get_id(),
                client=self.get_context().get_client_wrapper().get_client(),
                asset_ids=[self.get_id()],
            )
        except Exception as e:
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            error_msg = f"[ERROR] Exception during proxy_tag_assets: {e}"
            log(error_msg, level=LogLevel.ERROR)
            from immich_autotag.report.modification_kind import ModificationKind

            entry = tag_mod_report.add_modification(
                asset_wrapper=self,
                kind=ModificationKind.WARNING_TAG_ADDITION_TO_ASSET_FAILED,
                tag=tag,
                user=user_wrapper,
                extra={"error": error_msg},
            )
            return ModificationEntriesList(entries=[entry])
        log(f"[DEBUG] Response proxy_tag_assets: {response}", level=LogLevel.DEBUG)
        log(
            f"[INFO] Added tag '{tag_name}' to asset.id={self.get_id()}.",
            level=LogLevel.DEBUG,
        )
        from immich_autotag.report.modification_kind import ModificationKind

        entry = tag_mod_report.add_modification(
            kind=ModificationKind.ADD_TAG_TO_ASSET,
            asset_wrapper=self,
            tag=tag,
            user=user_wrapper,
        )
        return ModificationEntriesList(entries=[entry])

    @typechecked
    def _get_current_tag_ids(self) -> list[TagUUID]:
        """Returns the AssetUUIDs of the asset's current tags."""
        tags: list[TagWrapper] = self.get_tags()
        return [t.get_id() for t in tags]

    @typechecked
    def get_album_names(self) -> list[str]:
        """
        Returns the names of the albums this asset belongs to.
        """
        return self.get_context().get_albums_collection().album_names_for_asset(self)

    @typechecked
    def get_tag_names(self) -> list[str]:
        """
        Returns the names of the tags associated with this asset.
        """
        tag_names: list[str] | Unset = self._cache_entry.ensure_full_asset_loaded(
            self.get_context()
        ).get_tag_names()
        if isinstance(tag_names, Unset):
            raise ValueError(
                "Tags are UNSET; tags have not been loaded for this asset."
            )
        return tag_names

    @typechecked
    def get_classification_status(self) -> "MatchResultList":
        """
        Returns the comprehensive match results for the asset classification.

        Determines which classification rules matched the asset and returns the full
        MatchResultList with all matched rules, tags, and albums. This provides more
        detailed information than just the classification status.

        This is the primary method for classification evaluation. Use this instead
        of checking individual boolean properties.

        Returns:
            MatchResultList containing all matched rules and their details.
        """
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set: ClassificationRuleSet = (
            ClassificationRuleSet.get_rule_set_from_config_manager()
        )
        match_results: MatchResultList = rule_set.matching_rules(self)
        return match_results

    def get_original_file_name(self) -> Path:
        return self._cache_entry.get_original_file_name()

    def is_favorite(self) -> bool:
        return self._cache_entry.get_is_favorite()

    def get_created_at(self) -> datetime | str | None:
        return self._cache_entry.get_created_at()

    def get_id(self) -> AssetUUID:
        # Use get_uuid from cache_entry, which is the correct and safe method
        return self._cache_entry.get_uuid()

    def get_original_path(self) -> Path:
        # Ensure the return is a Path object
        orig = self._cache_entry.get_original_path()
        return orig

    def get_duplicate_id_as_uuid(self) -> DuplicateUUID | None:

        return self._cache_entry.get_duplicate_id_as_uuid()

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
    def check_unique_classification(self, *, fail_fast: bool = True) -> bool:
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

        # Determine classification status

        status = match_result_list.classification_status()

        if status.is_conflict():

            # Get details for error message
            match_detail = self.get_classification_match_detail()
            photo_url = get_immich_photo_url(self.get_id())
            n_rules_matched = len(match_result_list.rules())
            tags_matched_list = match_detail.tags_matched()
            albums_matched_list = match_detail.albums_matched()
            msg = (
                f"[ERROR] Asset id={self.get_id()} ({self.get_original_file_name()}) is classified by "
                f"{n_rules_matched} different rules (conflict). Matched tags={tags_matched_list}, "
                f"albums={albums_matched_list}\nLink: {photo_url}"
            )
            if fail_fast:
                raise Exception(msg)
            else:
                pass  # Fix for IndentationError if block is empty
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(msg, level=LogLevel.ERROR)
            return True
        return False

    # Callable is now imported at the module level

    @typechecked
    def _ensure_tag_for_classification_status(
        self,
        *,
        tag_name: str,
        should_have_tag_fn: Callable[[], bool],
        tag_present_reason: str,
        tag_absent_reason: str,
    ) -> ModificationEntriesList:
        """
        Generic method to manage classification-related tags.

        Args:
            tag_name: Name of the tag to manage.
            should_have_tag_fn: Callable that returns True if tag should be present.
            tag_present_reason: Log message reason when adding tag.
            tag_absent_reason: Log message reason when removing tag.

        Returns:
            ModificationEntriesList with the modifications performed (add/remove tag).
        """
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if should_have_tag_fn():
            if not self.has_tag(tag_name=tag_name):
                entries = self.add_tag_by_name(tag_name=tag_name)
                log(
                    f"[CLASSIFICATION] asset.id={self.get_id()} ({self.get_original_file_name()}) "
                    f"{tag_present_reason}. Tagged as '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
                return entries
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.get_id()} ({self.get_original_file_name()}) "
                    f"{tag_present_reason}. Tag '{tag_name}' already present.",
                    level=LogLevel.FOCUS,
                )
                return ModificationEntriesList()
        else:
            if self.has_tag(tag_name=tag_name):
                log(
                    f"[CLASSIFICATION] Removing tag '{tag_name}' from asset.id={self.get_id()} "
                    f"({self.get_original_file_name()}) because {tag_absent_reason}.",
                    level=LogLevel.FOCUS,
                )

                user_obj = UserResponseWrapper.load_current_user()
                entries = self.remove_tag_by_name(tag_name=tag_name, user=user_obj)
                return entries
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.get_id()} ({self.get_original_file_name()}) {tag_absent_reason}. Tag '{tag_name}' not present.",
                    level=LogLevel.FOCUS,
                )
                return ModificationEntriesList()

    @typechecked
    def _ensure_autotag_unknown_category(self) -> ModificationEntriesList:
        """
        Adds or removes the AUTOTAG_UNKNOWN_CATEGORY tag according to classification state.

        Tag management logic:
        - UNCLASSIFIED: Adds tag if not present (asset needs classification)
        - CLASSIFIED: Removes tag if present (asset has been classified)
        - CONFLICT: Removes tag if present (asset has classifications, even if conflicting)

        Idempotent: does nothing if already in correct state.
        Also logs and notifies the modification report.

        Returns:
            ModificationEntriesList with the modifications performed.
        """

        from immich_autotag.config.models import ClassificationConfig

        config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
        classification: ClassificationConfig = config.classification
        tag_name = classification.autotag_unknown
        if tag_name is None:
            from immich_autotag.logging.utils import log

            log(
                "[WARNING] autotag_unknown not set in config.classification; skipping tag management."
            )
            return ModificationEntriesList()
        match_results = self.get_classification_status()
        status = match_results.classification_status()
        return self._ensure_tag_for_classification_status(
            tag_name=tag_name,
            should_have_tag_fn=status.is_unclassified,
            tag_present_reason="is not classified",
            tag_absent_reason="it is now classified",
        )

    @typechecked
    def _ensure_autotag_conflict_category(
        self,
        *,
        status: "ClassificationStatus",
    ) -> ModificationEntriesList:
        """
        Adds or removes the AUTOTAG_CONFLICT_CATEGORY tag according to classification status.

        If status is CONFLICT, adds the tag if not present.
        If status is CLASSIFIED or UNCLASSIFIED (no conflict) and tag is present, removes it.

        Args:
            status: The ClassificationStatus determining if conflict tag should be present.

        Returns:
            ModificationEntriesList with the modifications performed.
        """

        from immich_autotag.config.models import ClassificationConfig

        config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
        classification: ClassificationConfig = config.classification
        tag_name = classification.autotag_conflict
        if tag_name is None:
            from immich_autotag.logging.utils import log

            log(
                "[WARNING] autotag_conflict not set in config.classification; skipping tag management."
            )
            return ModificationEntriesList()
        return self._ensure_tag_for_classification_status(
            tag_name=tag_name,
            should_have_tag_fn=status.is_conflict,
            tag_present_reason="is in classification conflict",
            tag_absent_reason=f"classification status is {status.value}",
        )

    def validate_and_update_classification(self) -> "ClassificationValidationResult":
        """
        Validates and updates asset classification state with proper tag management.

        Determines classification status (CLASSIFIED, CONFLICT, or UNCLASSIFIED) and:
        - Adds/removes 'unknown' tag if unclassified
        - Adds/removes 'conflict' tag if classification conflict exists

        This method is idempotent: calling it multiple times produces the same result.

        Returns:
            ClassificationValidationResult: Contains match results (cause) and modifications (consequence),
                along with has_tags and has_albums status.
        """
        tag_names = self.get_tag_names()
        album_names = self.get_album_names()

        # Get comprehensive classification status and update tags accordingly
        match_results = self.get_classification_status()
        status = match_results.classification_status()

        # Capture modifications from tag management
        modifications = ModificationEntriesList()
        unknown_entries = self._ensure_autotag_unknown_category()
        conflict_entries = self._ensure_autotag_conflict_category(status=status)
        modifications = modifications.extend(unknown_entries)
        modifications = modifications.extend(conflict_entries)

        # Log the classification result
        log(
            f"[CLASSIFICATION] Asset {self.get_id()} | Name: {self.get_original_file_name()} | "
            f"Favorite: {self.is_favorite()} | Tags: {', '.join(tag_names) if tag_names else '-'} | "
            f"Albums: {', '.join(album_names) if album_names else '-'} | Status: {status.value} | "
            f"Date: {self.get_created_at()} | original_path: {self.get_original_path()}",
            level=LogLevel.FOCUS,
        )

        from immich_autotag.assets.classification_validation_result import (
            ClassificationValidationResult,
        )

        return ClassificationValidationResult(
            match_results=match_results,
            modifications=modifications,
        )

    @typechecked
    def apply_tag_conversions(
        self,
        *,
        tag_conversions: TagConversions,
    ) -> ModificationEntriesList:
        """
        Applies each conversion by calling its apply_to_asset method.
        """
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        changes = ModificationEntriesList()
        for conv in tag_conversions:
            result: ModificationEntriesList | None = conv.apply_to_asset(self)
            if result:
                changes = changes.extend(result)
        if changes.has_changes():
            for entry in changes:
                log(
                    f"[TAG CONVERSION] {entry.kind.value.name} on asset {self.get_id()} ({self.get_original_file_name()})",
                    level=LogLevel.FOCUS,
                )
        else:
            log(
                f"[TAG CONVERSION] No tag changes performed on asset {self.get_id()} ({self.get_original_file_name()})",
                level=LogLevel.FOCUS,
            )
        log(
            f"[TAG CONVERSION] Tag conversion finished for asset {self.get_id()} ({self.get_original_file_name()})",
            level=LogLevel.FOCUS,
        )
        return changes

    @typechecked
    def try_detect_album_from_folders(self) -> str | None:
        """
        Attempts to detect a reasonable album name from the asset's folder path, according to the feature spec.
        Only runs if enable_album_detection_from_folders (from config) is True, the asset does not already belong to an album,
        and is not classified or conflicted. Returns the detected album name or None.
        Raises NotImplementedError for ambiguous cases.
        Improved: If the date folder is the parent of the containing folder, concatenate both (date + subfolder) for the album name.
        If the date is already in the containing folder, keep as before.
        """
        from immich_autotag.classification.classification_status import (
            ClassificationStatus,
        )

        config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
        if not config.album_detection_from_folders.enabled:
            return None

        # If already classified or conflicted by tag or album, skip
        match_results = self.get_classification_status()
        status = match_results.classification_status()
        match status:
            case ClassificationStatus.UNCLASSIFIED:
                # Proceed with album detection
                pass
            case ClassificationStatus.CLASSIFIED | ClassificationStatus.CONFLICT:
                # Asset already has classifications, don't try folder detection
                return None
            case _:
                raise NotImplementedError(f"Unhandled classification status: {status}")

        # If already in an album matching configured album patterns, skip
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        if rule_set.matches_any_album_of_asset(self):
            return None
        analyzer = AlbumFolderAnalyzer(self.get_original_path())
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

    # REMOVED: get_id_as_uuid, use get_id() for AssetUUID

    @typechecked
    def has_same_classification_tags_as(self, *, other: "AssetResponseWrapper") -> bool:
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

        url = self.get_immich_photo_url()
        return url

    def get_url(self) -> ParseResult:
        """
        Returns a ParseResult URL object for this asset.
        """

        url = self.get_immich_photo_url()
        return url

    def get_uuid(self) -> "AssetUUID":
        return self.get_id()

    # Removed duplicate method get_album_names

    @typechecked
    def get_duplicate_wrappers(self) -> list["AssetResponseWrapper"]:
        """
        Returns a list of AssetResponseWrapper objects for all duplicates of this asset (excluding itself).
        """

        context = self.get_context()
        duplicate_id_or_none = self.get_duplicate_id_as_uuid()
        # If there's no duplicate ID, this asset has no duplicates
        if duplicate_id_or_none is None:
            return []
        duplicate_id: DuplicateUUID = duplicate_id_or_none
        wrappers: list[AssetResponseWrapper] = []
        group = context.get_duplicates_collection().get_group(duplicate_id)
        for dup_id in group:
            if dup_id == self.get_uuid():
                continue
            dup_asset = context.get_asset_manager().get_asset(dup_id, context)
            if dup_asset is not None:
                wrappers.append(dup_asset)
        return wrappers

    @typechecked
    def ensure_autotag_duplicate_album_conflict(
        self,
        *,
        conflict: bool,
        user: "UserResponseWrapper | None" = None,
        duplicate_id: DuplicateUUID,
    ) -> None:
        """
        Adds or removes the AUTOTAG_DUPLICATE_ALBUM_CONFLICT tag according to duplicate album conflict state.
        If there is conflict, adds the tag if not present. If no conflict and tag is present, removes it.
        Also handles the per-duplicate-set tag if duplicate_id is provided (UUID).
        """
        config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
        tag_name = None
        # Use explicit type and direct access for duplicate_processing
        if config and config.duplicate_processing is not None:
            tag_name = config.duplicate_processing.autotag_album_conflict
        if tag_name is None:
            from immich_autotag.logging.utils import log

            log(
                "[WARNING] autotag_album_conflict not set in config.duplicate_processing; skipping tag management."
            )
            return
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        # Generic tag
        if conflict:
            if not self.has_tag(tag_name=tag_name):
                self.add_tag_by_name(tag_name=tag_name)
                log(
                    f"asset.id={self.get_id()} ({self.get_original_file_name()}) is in duplicate album conflict. "
                    f"Tagged as '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
        else:
            if self.has_tag(tag_name=tag_name):
                log(
                    f"Removing tag '{tag_name}' from asset.id={self.get_id()} "
                    f"because duplicate album conflict is resolved.",
                    level=LogLevel.FOCUS,
                )
                self.remove_tag_by_name(tag_name=tag_name, user=user)
        # Per-duplicate-set tag
        if duplicate_id:
            tag_for_set = f"{tag_name}_{str(duplicate_id)}"
            if conflict:
                if not self.has_tag(tag_name=tag_for_set):
                    self.add_tag_by_name(tag_name=tag_for_set)
                    log(
                        f"asset.id={self.get_id()} ({self.get_original_file_name()}) is in duplicate album conflict (set {duplicate_id}). Tagged as '{tag_for_set}'.",
                        level=LogLevel.FOCUS,
                    )
            else:
                if self.has_tag(tag_name=tag_for_set):
                    log(
                        f"Removing tag '{tag_for_set}' from asset.id={self.get_id()} because duplicate album conflict (set {duplicate_id}) is resolved.",
                        level=LogLevel.FOCUS,
                    )
                    self.remove_tag_by_name(tag_name=tag_for_set, user=user)

    @typechecked
    def ensure_autotag_album_detection_conflict(
        self,
        *,
        conflict: bool,
        candidate_folders: list[str] | None = None,
        user: "UserResponseWrapper | None" = None,
    ) -> None:
        """
        Adds or removes the AUTOTAG_ALBUM_DETECTION_CONFLICT tag according to album detection conflict state.
        If there is conflict (multiple candidate folders), adds the tag if not present.
        If no conflict and tag is present, removes it.
        """

        config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
        tag_name = None
        # Use explicit type and direct access for duplicate_processing
        if config and config.duplicate_processing is not None:
            tag_name = config.duplicate_processing.autotag_album_detection_conflict
        if tag_name is None:
            from immich_autotag.logging.utils import log

            log(
                "[WARNING] autotag_album_detection_conflict not set in config.duplicate_processing; skipping tag management."
            )
            return
        if not tag_name:
            return  # Tag not configured, skip

        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if conflict:
            if not self.has_tag(tag_name=tag_name):
                self.add_tag_by_name(tag_name=tag_name)
                folders_str = str(candidate_folders) if candidate_folders else "unknown"
                log(
                    f"[ALBUM DETECTION] Asset '{self.get_original_file_name()}' ({self.get_id()}) has multiple candidate folders: "
                    f"{folders_str}. Tagged with '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
                # Register in modification report
                from immich_autotag.report.modification_kind import ModificationKind
                from immich_autotag.report.modification_report import ModificationReport

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
            if self.has_tag(tag_name=tag_name):
                log(
                    f"[ALBUM DETECTION] Removing tag '{tag_name}' from asset '{self.get_original_file_name()}' ({self.get_id()}) "
                    f"because album detection conflict is resolved.",
                    level=LogLevel.FOCUS,
                )
                self.remove_tag_by_name(tag_name=tag_name, user=user)

    @typechecked
    def format_info(self) -> str:
        lines = [f"Asset {self.get_id()} | {self.get_original_file_name()}"]
        try:
            link = self.get_immich_photo_url().geturl()
        except Exception:
            link = "(no link)"
        lines.append(f"  Link: {link}")
        try:
            created_at = self.get_created_at()
        except AttributeError:
            created_at = None
        lines.append(f"  created_at: {created_at}")
        try:
            file_created_at = None
            state = self._cache_entry.get_state()
            dates = state.get_dates()
            if len(dates) > 1:
                file_created_at = dates[1]
        except Exception:
            file_created_at = None
        lines.append(f"  file_created_at: {file_created_at}")
        # exif_created_at is not present in AssetResponseDto
        lines.append("  exif_created_at: (not available)")
        # Print the correct updated_at value from AssetDtoState
        state = self._cache_entry.get_state()
        updated_at = state.get_loaded_at()
        lines.append(f"  updated_at: {updated_at}")
        lines.append(f"  Tags: {self.get_tag_names()}")
        lines.append(f"  Albums: {self.get_album_names()}")
        try:
            original_path = self.get_original_path()
        except AttributeError:
            original_path = None
        lines.append(f"  Path: {original_path}")
        return "\n".join(lines)

    @classmethod
    def from_id(
        cls, asset_id: "AssetUUID", context: "ImmichContext"
    ) -> "AssetResponseWrapper":
        """
        Gets an AssetResponseWrapper by ID, delegating the retrieval logic to AssetCacheEntry._from_cache_or_api.
        Accepts either AssetUUID or uuid.UUID, but always converts to AssetUUID for type safety.
        """
        from immich_autotag.assets.asset_cache_entry import AssetCacheEntry

        entry = AssetCacheEntry.from_cache_or_api(asset_id)
        return cls(context, entry)
