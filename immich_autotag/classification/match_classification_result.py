from typing import List

import attrs

from immich_autotag.classification.match_result_list import MatchResultList


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class MatchClassificationResult:
    tags_matched: List[str] = attrs.field(validator=attrs.validators.instance_of(list))
    albums_matched: List[str] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    @classmethod
    def from_match_result_list(
        cls, match_result_list: MatchResultList
    ) -> "MatchClassificationResult":
        """
        Aggregate tags_matched and albums_matched from a MatchResultList object.
        """
        from typeguard import typechecked

        @typechecked
        def _aggregate(
            match_result_list: MatchResultList,
        ) -> tuple[list[str], list[str]]:
            tags = []
            albums = []
            for m in match_result_list.matches:
                tags.extend(m.tags_matched)
                albums.extend(m.albums_matched)
            return tags, albums

        tags, albums = _aggregate(match_result_list)
        return cls(tags_matched=tags, albums_matched=albums)

    def any(self) -> bool:
        return bool(self.tags_matched or self.albums_matched)
