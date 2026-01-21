from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

import attrs
from typeguard import typechecked

from immich_autotag.config.models import ClassificationRule


@attrs.define(auto_attribs=True, slots=True, frozen=True, eq=True)
class ClassificationRuleWrapper:

    rule: ClassificationRule = attrs.field(
        validator=attrs.validators.instance_of(ClassificationRule)
    )

    def __attrs_post_init__(self):
        """
        Validates the rule configuration.
        A rule must have at least one criterion (tags, albums, or asset_links).
        Multiple criteria are combined with OR logic: the rule matches if ANY criterion is satisfied.
        """
        tag_names = self.rule.tag_names
        album_patterns = self.rule.album_name_patterns
        asset_links = self.rule.asset_links

        has_tags = bool(tag_names)
        has_albums = bool(album_patterns)
        has_asset_links = bool(asset_links)

        # At least one criterion must be present
        if not (has_tags or has_albums or has_asset_links):
            raise ValueError(
                f"ClassificationRuleWrapper: Each rule must have at least one criterion "
                f"(tag_names, album_name_patterns, or asset_links). Rule: {self.rule}"
            )

    @typechecked
    def has_tag(self, tag_name: str) -> bool:
        return self.rule.tag_names is not None and tag_name in self.rule.tag_names

    @typechecked
    def matches_album(self, album_name: str) -> bool:
        if not self.rule.album_name_patterns:
            return False
        import re

        return any(
            re.match(pattern, album_name) for pattern in self.rule.album_name_patterns
        )

    @typechecked
    def matches_asset(
        self, asset_wrapper: "AssetResponseWrapper"
    ) -> "MatchResult | None":
        """
        Returns a MatchResult for this rule and the given asset (with lists of matching tags, albums, and asset_links), or None if no match.
        """
        from immich_autotag.classification.match_result import MatchResult

        asset_tags = set(asset_wrapper.get_tag_names())
        album_names = set(asset_wrapper.get_album_names())
        tags_matched = [tag for tag in asset_tags if self.has_tag(tag)]
        albums_matched = [album for album in album_names if self.matches_album(album)]

        # Check asset_links (UUIDs)
        asset_link_uuids = self.extract_uuids_from_asset_links()
        asset_uuid = asset_wrapper.id_as_uuid
        asset_links_matched = []
        if asset_link_uuids and asset_uuid is not None:
            if asset_uuid in asset_link_uuids:
                asset_links_matched = [str(asset_uuid)]

        if not tags_matched and not albums_matched and not asset_links_matched:
            return None
        return MatchResult(
            rule=self,
            tags_matched=tags_matched,
            albums_matched=albums_matched,
            asset_links_matched=asset_links_matched,
        )

    @typechecked
    def is_focused(self) -> bool:
        """
        Returns True if this rule targets concrete assets via `asset_links`.
        Filtering by tags or albums alone does not count as focused.
        """
        return len(self.extract_uuids_from_asset_links()) > 0

    @typechecked
    def extract_uuids_from_asset_links(self) -> list["UUID"]:
        """
        Extracts UUIDs from the asset_links of this rule.
        Accepts complete URLs or direct UUIDs.
        """
        import re
        from uuid import UUID

        if not self.rule.asset_links:
            return []

        uuids = []
        uuid_pattern = re.compile(
            r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})"
        )

        for link in self.rule.asset_links:
            match = uuid_pattern.search(link)
            if not match:
                raise RuntimeError(
                    f"[ERROR] Could not extract asset ID from link: {link}"
                )
            try:
                asset_uuid = UUID(match.group(1))
                uuids.append(asset_uuid)
            except Exception:
                raise RuntimeError(
                    f"[ERROR] Invalid asset ID (not a valid UUID): {match.group(1)}"
                )

        return uuids

    @typechecked
    def remove_matches(
        self, asset_wrapper: "AssetResponseWrapper", match_result: "MatchResult"
    ) -> list[str]:
        """
        Removes all tags and albums from the asset that matched this rule (based on the MatchResult).
        Returns a list of changes made.
        """
        changes = []
        # Remove matched tags
        for tag in match_result.tags_matched:
            if asset_wrapper.has_tag(tag):
                asset_wrapper.remove_tag_by_name(tag)
                changes.append(f"Removed matched tag '{tag}'")
        # Remove matched albums (if logic exists for it)
        # for album in match_result.albums_matched:
        #     if album in asset_wrapper.get_album_names():
        #         ... # logic to remove asset from album
        #         changes.append(f"Removed asset from matched album '{album}'")
        return changes

    # You can add more utility methods as needed
