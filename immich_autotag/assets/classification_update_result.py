from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationUpdateResult:
    has_tags: bool
    has_albums: bool
