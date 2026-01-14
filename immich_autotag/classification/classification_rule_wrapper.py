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
        tag_names = self.rule.tag_names
        album_patterns = self.rule.album_name_patterns
        has_tags = bool(tag_names)
        has_albums = bool(album_patterns)
        if has_tags and has_albums:
            raise NotImplementedError(
                f"ClassificationRuleWrapper: Each rule must have either tag_names or a single album_name_pattern, not both. Rule: {self.rule}"
            )
        if not has_tags and not has_albums:
            raise ValueError(
                f"ClassificationRuleWrapper: Each rule must have either tag_names or a single album_name_pattern. Rule: {self.rule}"
            )
        if has_albums:
            if not isinstance(album_patterns, list) or len(album_patterns) != 1:
                raise NotImplementedError(
                    f"ClassificationRuleWrapper: album_name_patterns must be a list with exactly one pattern. Rule: {self.rule}"
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
    def matches_asset(self, asset_wrapper: 'AssetResponseWrapper') -> 'MatchResult | None':
        """
        Returns a MatchResult for this rule and the given asset (with lists of matching tags and albums), or None if no match.
        """
        from immich_autotag.classification.match_result import MatchResult
        asset_tags = set(asset_wrapper.get_tag_names())
        album_names = set(asset_wrapper.get_album_names())
        tags_matched = [tag for tag in asset_tags if self.has_tag(tag)]
        albums_matched = [album for album in album_names if self.matches_album(album)]
        if not tags_matched and not albums_matched:
            return None
        return MatchResult(rule=self, tags_matched=tags_matched, albums_matched=albums_matched)

    @typechecked
    def extract_uuids_from_asset_links(self) -> list['UUID']:
        """
        Extrae UUIDs de los asset_links de esta regla.
        Acepta URLs completas o UUIDs directos.
        """
        from uuid import UUID
        import re
        
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
    # You can add more utility methods as needed
