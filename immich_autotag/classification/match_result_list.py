from typing import List

import attr
from typeguard import typechecked

from immich_autotag.classification.match_result import MatchResult


@attr.s(auto_attribs=True, slots=True, kw_only=True, frozen=True)
class MatchResultList:
    matches: List[MatchResult] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(MatchResult),
            iterable_validator=attr.validators.instance_of(list),
        )
    )

    @typechecked
    def __len__(self) -> int:
        return len(self.matches)

    @typechecked
    def __getitem__(self, idx: int) -> MatchResult:
        return self.matches[idx]

    @typechecked
    def tags(self) -> list[str]:
        tags = []
        for m in self.matches:
            tags.extend(m.tags_matched)
        return tags

    @typechecked
    def albums(self) -> list[str]:
        albums = []
        for m in self.matches:
            albums.extend(m.albums_matched)
        return albums

    @typechecked
    def rules(self) -> list:
        return [m.rule for m in self.matches]
