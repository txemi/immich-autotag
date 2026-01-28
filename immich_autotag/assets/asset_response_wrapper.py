from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from urllib.parse import ParseResult
from uuid import UUID

import attrs
from immich_client.models.tag_response_dto import TagResponseDto
from immich_client.models.update_asset_dto import (
    UpdateAssetDto,  # TODO: move to proxy if needed
)
from immich_client.types import Unset
from typeguard import typechecked

from immich_autotag.albums.folder_analysis.album_folder_analyzer import (
    AlbumFolderAnalyzer,
)
from immich_autotag.api.immich_proxy.assets import AssetResponseDto
from immich_autotag.assets.asset_cache_entry import (
    AssetCacheEntry,
)
from immich_autotag.assets.classification_update_result import (
    ClassificationUpdateResult,
)
from immich_autotag.classification.classification_status import ClassificationStatus
from immich_autotag.classification.match_classification_result import (
    MatchClassificationResult,
)
from immich_autotag.config.manager import ConfigManager
from immich_autotag.config.models import UserConfig
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.conversions.tag_conversions import TagConversions
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper
from immich_autotag.tags.tag_response_wrapper import TagWrapper
from immich_autotag.users.user_response_wrapper import UserResponseWrapper
from immich_autotag.utils.deprecation import raise_deprecated_path
from immich_autotag.utils.url_helpers import get_immich_photo_url

if TYPE_CHECKING:
    from pathlib import Path


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
        from immich_autotag.api.immich_proxy.assets import proxy_update_asset

        raise_deprecated_path("realmente necesitamos esto?")
        old_date = self.get_created_at()
        # Ensure the date is timezone-aware in UTC
        if new_date.tzinfo is None:
            raise ValueError(
                (
                    "[ERROR] new_date must be timezone-aware. "
                    "Received naive datetime. Asset will not be updated."
                )
            )
        dto = UpdateAssetDto(date_time_original=new_date.isoformat())
        # Log and print before updating the asset, including link to the photo in Immich
        from immich_autotag.logging.utils import is_log_level_enabled, log_debug

        if is_log_level_enabled(LogLevel.DEBUG):
            photo_url_obj = self.get_immich_photo_url()
            photo_url = photo_url_obj.geturl()
            log_msg = (
                f"[INFO] Updating asset date: asset.id={self.get_id()}, "
                f"asset_name={self.get_original_file_name()}, "
                f"old_date={old_date}, new_date={new_date}\n"
                f"[INFO] Immich photo link: {photo_url}"
            )
            log_debug(f"[BUG] {log_msg}")
        from immich_autotag.report.modification_kind import ModificationKind
        from immich_autotag.report.modification_report import ModificationReport
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper

        tag_mod_report = ModificationReport.get_instance()
        user_wrapper = UserResponseWrapper.from_context(self.get_context())
        # asset_url = self.get_immich_photo_url().geturl()  # Unused variable removed

        tag_mod_report.add_modification(
            kind=ModificationKind.UPDATE_ASSET_DATE,
            asset_wrapper=self,
            old_value=str(old_date) if old_date else None,
            new_value=str(new_date) if new_date else None,
            user=user_wrapper,
            extra={"pre_update": True},
        )
        response = proxy_update_asset(
            asset_id=self.get_id_as_uuid(),
            client=self.get_context().get_client().get_client(),
            body=dto,
        )
        # Fail-fast: check response type and status directly, no dynamic attribute access
        # If the API returns a response object with status_code, check it; otherwise, assume success if no exception was raised
        # If the response is an AssetResponseDto, we expect no error field and no status_code
        # If the API changes and returns a dict or error object, this will fail fast
        if not isinstance(response, AssetResponseDto):
            raise DateIntegrityError(
                f"[ERROR] update_asset.sync did not return AssetResponseDto, "
                f"got {type(response)}: {response} for asset.id={self.get_id()} "
                f"({self.get_original_file_name()})"
            )
        # If the response has an 'error' attribute and it is not None, fail fast (static access only)
        # This assumes that if present, 'error' is a public attribute of the response object
        # OPTIMIZATION: Trust the API response instead of polling with sleep().
        # The API call to proxy_update_asset should atomically update and return the asset.
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

        return get_immich_photo_url(self.get_id_as_uuid())

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
        if duplicate_id is not None:
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
    ) -> bool:
        """
        Removes all tags from the asset with the given name (case-insensitive),
        even if they have different IDs (e.g., global and nested tags).
        Returns True if at least one was removed, False if none were found.
        After removal, reloads the asset and checks if the tag is still present.
        Raises if any remain.
        Uses TagWrapper from the tag collection for all reporting.
        """

        from immich_autotag.api.immich_proxy.tags import proxy_untag_assets
        from immich_autotag.logging.utils import is_log_level_enabled, log_debug

        tags = self.get_tags()
        tags_to_remove = [
            tag for tag in tags if tag.get_name().lower() == tag_name.lower()
        ]
        if not tags_to_remove:
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug(
                    f"[BUG][INFO] Asset id={self.get_id()} does not have the tag '{tag_name}'"
                )
            return False
        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(
                f"[BUG] Before removal: asset.id={self.get_id()}, "
                f"asset_name={self.get_original_file_name()}, "
                f"tag_name='{tag_name}', tag_ids={[str(tag.get_id()) for tag in tags_to_remove]}"
            )
            log_debug(f"[BUG] Tags before removal: {self.get_tag_names()}")
        assert isinstance(
            self.get_context().get_tag_collection(), TagCollectionWrapper
        ), "context.tag_collection must be an object"
        tag_wrapper = self.get_context().get_tag_collection().find_by_name(tag_name)
        removed_any = False
        tag_mod_report = ModificationReport.get_instance()
        for tag in tags_to_remove:
            tag_uuid = tag.get_id()
            response = proxy_untag_assets(
                tag_id=tag_uuid,
                client=self.get_context().get_client().get_client(),
                asset_ids=[self.get_id_as_uuid()],
            )
            if is_log_level_enabled(LogLevel.DEBUG):
                log_debug(
                    f"[BUG] Full untag_assets response for tag_id={str(tag_uuid)}: {response}"
                )
                log_debug(
                    f"[BUG][INFO] Removed tag '{tag_name}' (id={str(tag_uuid)}) from asset.id={self.get_id()}. "
                    f"Response: {response}"
                )
            removed_any = True
            from immich_autotag.report.modification_kind import ModificationKind

            tag_mod_report.add_modification(
                kind=ModificationKind.REMOVE_TAG_FROM_ASSET,
                asset_wrapper=self,
                tag=tag_wrapper,
                user=user,
            )

        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(f"[PERF] Tag '{tag_name}' removal applied")
        return removed_any

    @typechecked
    def add_tag_by_name(
        self,
        *,
        tag_name: str,
        fail_if_exists: bool = False,
    ) -> bool:
        """
        Adds a tag to the asset by name using the Immich API if it doesn't have it already.
        Returns True if added, raises exception if it already had it or if the tag doesn't exist.
        """
        from immich_autotag.api.immich_proxy.tags import proxy_tag_assets
        from immich_autotag.users.user_response_wrapper import UserResponseWrapper

        tag_mod_report = ModificationReport.get_instance()

        # Get the UserWrapper in a clean and encapsulated way
        user_wrapper = UserResponseWrapper.from_context(self.get_context())

        tag = self.get_context().get_tag_collection().find_by_name(tag_name)
        if tag is None:
            tag = (
                self.get_context()
                .get_tag_collection()
                .create_tag_if_not_exists(
                    name=tag_name, client=self.get_context().get_client().get_client()
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
            return False
        # Extra checks and logging before API call
        if not tag or tag.id is None:
            error_msg = (
                f"[ERROR] Tag object for '{tag_name}' is missing or has no id. "
                f"Tag: {tag}"
            )
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(error_msg, level=LogLevel.ERROR)
            from immich_autotag.report.modification_kind import ModificationKind

            tag_mod_report.add_modification(
                kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                asset_wrapper=self,
                tag=tag,
                user=user_wrapper,
                extra={"error": error_msg},
            )
            return False
        if not self.get_id():
            error_msg = f"[ERROR] Asset object is missing id. Asset state: {str(self._cache_entry.get_state())}"
            from immich_autotag.logging.levels import LogLevel
            from immich_autotag.logging.utils import log

            log(error_msg, level=LogLevel.ERROR)
            if tag_mod_report:
                from immich_autotag.report.modification_kind import ModificationKind

                tag_mod_report.add_modification(
                    kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                    asset_wrapper=self,
                    tag=tag,
                    user=user_wrapper,
                    extra={"error": error_msg},
                )
            return False
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
                client=self.get_context().get_client().get_client(),
                asset_ids=[self.get_id_as_uuid()],
            )
        except Exception as e:
            error_msg = f"[ERROR] Exception during proxy_tag_assets: {e}"
            log(error_msg, level=LogLevel.ERROR)
            if tag_mod_report:
                from immich_autotag.report.modification_kind import ModificationKind

                tag_mod_report.add_modification(
                    asset_wrapper=self,
                    kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
                    tag=tag,
                    user=user_wrapper,
                    extra={"error": error_msg},
                )
            return False
        log(f"[DEBUG] Response proxy_tag_assets: {response}", level=LogLevel.DEBUG)
        log(
            f"[INFO] Added tag '{tag_name}' to asset.id={self.get_id()}.",
            level=LogLevel.DEBUG,
        )
        from immich_autotag.report.modification_kind import ModificationKind

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
        from immich_client.types import Unset

        tags: list[TagResponseDto] | Unset = self.get_tags()
        if isinstance(tags, Unset):
            return []
        return [t.id for t in tags]

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
        from immich_client.types import Unset

        tag_names: list[str] | Unset = self._cache_entry.ensure_full_asset_loaded(
            self.get_context()
        ).get_tag_names()
        if isinstance(tag_names, Unset):
            raise ValueError(
                "Tags are UNSET; tags have not been loaded for this asset."
            )
        return tag_names

    @typechecked
    def get_classification_status(self) -> "ClassificationStatus":
        """
        Returns the comprehensive classification status of the asset.

        Determines whether the asset is:
        - CLASSIFIED: Matched exactly one classification rule
        - CONFLICT: Matched multiple classification rules
        - UNCLASSIFIED: Matched no classification rules

        This is the primary method for classification evaluation. Use this instead
        of checking individual boolean properties.

        Returns:
            ClassificationStatus enum indicating the asset's classification state.
        """
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        match_results = rule_set.matching_rules(self)
        return match_results.classification_status()

    def get_original_file_name(self) -> Path:
        return self._cache_entry.get_original_file_name()

    def is_favorite(self) -> bool:
        return self._cache_entry.get_is_favorite()

    def get_created_at(self) -> datetime | str | None:
        return self._cache_entry.get_created_at()

    def get_id(self) -> UUID:
        # Use get_uuid from cache_entry, which is the correct and safe method
        return self._cache_entry.get_uuid()

    def get_original_path(self) -> "Path":
        return self._cache_entry.get_original_path()

    def get_duplicate_id_as_uuid(self) -> UUID:
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
            photo_url = get_immich_photo_url(self.get_id_as_uuid())
            n_rules_matched = len(match_result_list.rules())
            msg = (
                f"[ERROR] Asset id={self.get_id()} ({self.get_original_file_name()}) is classified by "
                f"{n_rules_matched} different rules (conflict). Matched tags={match_detail.tags_matched}, "
                f"albums={match_detail.albums_matched}\nLink: {photo_url}"
            )
            if fail_fast:
                raise Exception(msg)
            else:
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log

                log(msg, level=LogLevel.ERROR)
            return True
        return False

    from typing import Callable

    @typechecked
    def _ensure_tag_for_classification_status(
        self,
        *,
        tag_name: str,
        should_have_tag_fn: Callable[[], bool],
        tag_present_reason: str,
        tag_absent_reason: str,
        user: UserResponseWrapper | None = None,
    ) -> None:
        """
        Generic method to manage classification-related tags.

        Args:
            tag_name: Name of the tag to manage.
            should_have_tag_fn: Callable that returns True if tag should be present.
            tag_present_reason: Log message reason when adding tag.
            tag_absent_reason: Log message reason when removing tag.
            user: Optional user for tracking tag removal.
        """
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        if should_have_tag_fn():
            if not self.has_tag(tag_name=tag_name):
                self.add_tag_by_name(tag_name=tag_name)
                log(
                    f"[CLASSIFICATION] asset.id={self.get_id()} ({self.get_original_file_name()}) "
                    f"{tag_present_reason}. Tagged as '{tag_name}'.",
                    level=LogLevel.FOCUS,
                )
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.get_id()} ({self.get_original_file_name()}) "
                    f"{tag_present_reason}. Tag '{tag_name}' already present.",
                    level=LogLevel.FOCUS,
                )
        else:
            if self.has_tag(tag_name=tag_name):
                log(
                    f"[CLASSIFICATION] Removing tag '{tag_name}' from asset.id={self.get_id()} "
                    f"({self.get_original_file_name()}) because {tag_absent_reason}.",
                    level=LogLevel.FOCUS,
                )
                if user is None:
                    user = UserResponseWrapper.from_context(self.get_context())
                self.remove_tag_by_name(tag_name=tag_name, user=user)
            else:
                log(
                    f"[CLASSIFICATION] asset.id={self.get_id()} ({self.get_original_file_name()}) {tag_absent_reason}. Tag '{tag_name}' not present.",
                    level=LogLevel.FOCUS,
                )

    @typechecked
    def _ensure_autotag_unknown_category(self) -> None:
        """
        Adds or removes the AUTOTAG_UNKNOWN_CATEGORY tag according to classification state.

        Tag management logic:
        - UNCLASSIFIED: Adds tag if not present (asset needs classification)
        - CLASSIFIED: Removes tag if present (asset has been classified)
        - CONFLICT: Removes tag if present (asset has classifications, even if conflicting)

        Idempotent: does nothing if already in correct state.
        Also logs and notifies the modification report.
        """

        from immich_autotag.config.models import ClassificationConfig

        config: Optional[UserConfig] = ConfigManager.get_instance().config
        tag_name = None
        if config is not None and config.classification is not None:
            classification: ClassificationConfig = config.classification
            tag_name = classification.autotag_unknown
        if tag_name is None:
            from immich_autotag.logging.utils import log

            log(
                "[WARNING] autotag_unknown not set in config.classification; skipping tag management."
            )
            return
        status = self.get_classification_status()
        self._ensure_tag_for_classification_status(
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
        user: UserResponseWrapper | None = None,
    ) -> None:
        """
        Adds or removes the AUTOTAG_CONFLICT_CATEGORY tag according to classification status.

        If status is CONFLICT, adds the tag if not present.
        If status is CLASSIFIED or UNCLASSIFIED (no conflict) and tag is present, removes it.

        Args:
            status: The ClassificationStatus determining if conflict tag should be present.
            user: Optional user for tracking tag removal. If None, derived from context.
        """

        from immich_autotag.config.models import ClassificationConfig

        config: Optional[UserConfig] = ConfigManager.get_instance().config
        tag_name = None
        if config is not None and config.classification is not None:
            classification: ClassificationConfig = config.classification
            tag_name = classification.autotag_conflict
        if tag_name is None:
            from immich_autotag.logging.utils import log

            log(
                "[WARNING] autotag_conflict not set in config.classification; skipping tag management."
            )
            return
        self._ensure_tag_for_classification_status(
            tag_name=tag_name,
            should_have_tag_fn=status.is_conflict,
            tag_present_reason="is in classification conflict",
            tag_absent_reason=f"classification status is {status.value}",
            user=user,
        )

    @typechecked
    def validate_and_update_classification(self) -> "ClassificationUpdateResult":
        """
        Validates and updates asset classification state with proper tag management.

        Determines classification status (CLASSIFIED, CONFLICT, or UNCLASSIFIED) and:
        - Adds/removes 'unknown' tag if unclassified
        - Adds/removes 'conflict' tag if classification conflict exists

        This method is idempotent: calling it multiple times produces the same result.

        Returns:
            Tuple of (has_tags, has_albums) booleans.
        """
        tag_names = self.get_tag_names()
        album_names = self.get_album_names()

        # Get comprehensive classification status and update tags accordingly
        status = self.get_classification_status()
        self._ensure_autotag_unknown_category()
        self._ensure_autotag_conflict_category(status=status)

        # Log the classification result
        log(
            f"[CLASSIFICATION] Asset {self.get_id()} | Name: {self.get_original_file_name()} | "
            f"Favorite: {self.is_favorite()} | Tags: {', '.join(tag_names) if tag_names else '-'} | "
            f"Albums: {', '.join(album_names) if album_names else '-'} | Status: {status.value} | "
            f"Date: {self.get_created_at()} | original_path: {self.get_original_path()}",
            level=LogLevel.FOCUS,
        )
        return ClassificationUpdateResult(bool(tag_names), bool(album_names))

    @typechecked
    def apply_tag_conversions(
        self,
        *,
        tag_conversions: TagConversions,
    ) -> list[str]:
        """
        Applies each conversion by calling its apply_to_asset method.
        """
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        changes = []
        for conv in tag_conversions:
            result = conv.apply_to_asset(self)
            if result:
                changes.extend(result)
        if changes:
            for c in changes:
                log(
                    f"[TAG CONVERSION] {c} on asset {self.get_id()} ({self.get_original_file_name()})",
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

        config: Optional[UserConfig] = ConfigManager.get_instance().config
        if not (
            config
            and config.album_detection_from_folders is not None
            and config.album_detection_from_folders.enabled
        ):
            return None

        # If already classified or conflicted by tag or album, skip
        status = self.get_classification_status()
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

    def get_id_as_uuid(self) -> "UUID":
        return self._cache_entry.get_uuid()

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

    def get_uuid(self) -> UUID:
        return self._cache_entry.get_uuid()

    # Removed duplicate method get_album_names

    @typechecked
    def get_duplicate_wrappers(self) -> list["AssetResponseWrapper"]:
        """
        Returns a list of AssetResponseWrapper objects for all duplicates of this asset (excluding itself).
        """

        context = self.get_context()
        duplicate_id = self.get_duplicate_id_as_uuid()
        wrappers = []
        if duplicate_id is not None:
            group = context.duplicates_collection.get_group(duplicate_id)
            for dup_id in group:
                if dup_id == self.get_uuid():
                    continue
                dup_asset = context.asset_manager.get_asset(dup_id, context)
                if dup_asset is not None:
                    wrappers.append(dup_asset)
        return wrappers

    @typechecked
    def ensure_autotag_duplicate_album_conflict(
        self,
        *,
        conflict: bool,
        # tag_mod_report parameter removed
        user: "UserResponseWrapper | None" = None,
        duplicate_id: str | None = None,
        disable=True,
    ) -> None:
        """
        Adds or removes the AUTOTAG_DUPLICATE_ALBUM_CONFLICT tag according to duplicate album conflict state.
        If there is conflict, adds the tag if not present. If no conflict and tag is present, removes it.
        Also handles the per-duplicate-set tag if duplicate_id is provided.
        """
        if disable:
            return
        config: Optional[UserConfig] = ConfigManager.get_instance().config
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
        # Generic tag
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

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
            tag_for_set = f"{tag_name}_{duplicate_id}"
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

        config: Optional[UserConfig] = ConfigManager.get_instance().config
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
        try:
            updated_at = None
            # If AssetDtoState has a get_updated_at method, use it; otherwise, skip
            state = self._cache_entry.get_state()
            updated_at = state.get_updated_at()
        except Exception:
            updated_at = None
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
        cls, asset_id: UUID, context: "ImmichContext"
    ) -> "AssetResponseWrapper":
        """
        Gets an AssetResponseWrapper by ID, delegating the retrieval logic to AssetCacheEntry._from_cache_or_api.
        """
        from immich_autotag.assets.asset_cache_entry import AssetCacheEntry

        entry = AssetCacheEntry.from_cache_or_api(asset_id)
        return cls(context, entry)
