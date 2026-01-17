"""
Classification status enum and utilities for determining asset classification state.

This module provides a clear, type-safe way to determine if an asset is:
- Classified by exactly one rule
- In conflict (multiple rules matched)
- Unclassified (no rules matched)
"""

from enum import Enum
from typing import TYPE_CHECKING

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.classification.match_result_list import MatchResultList


class ClassificationStatus(Enum):
    """Represents the classification state of an asset based on matched rules."""

    CLASSIFIED = "classified"
    """Asset matched exactly one classification rule."""

    CONFLICT = "conflict"
    """Asset matched multiple classification rules (conflict situation)."""

    UNCLASSIFIED = "unclassified"
    """Asset matched no classification rules."""

    @typechecked
    def is_classified(self) -> bool:
        """Returns True if asset is classified (exactly one rule matched)."""
        return self == ClassificationStatus.CLASSIFIED

    @typechecked
    def is_conflict(self) -> bool:
        """Returns True if asset has classification conflict (multiple rules matched)."""
        return self == ClassificationStatus.CONFLICT

    @typechecked
    def is_unclassified(self) -> bool:
        """Returns True if asset is unclassified (no rules matched)."""
        return self == ClassificationStatus.UNCLASSIFIED

    @staticmethod
    @typechecked
    def from_match_results(match_results: "MatchResultList") -> "ClassificationStatus":
        """
        Determines classification status from match results.

        Args:
            match_results: The result of matching classification rules against an asset.

        Returns:
            ClassificationStatus enum value indicating the asset's classification state.
        """
        num_rules_matched = len(match_results.rules())

        if num_rules_matched == 1:
            return ClassificationStatus.CLASSIFIED
        elif num_rules_matched > 1:
            return ClassificationStatus.CONFLICT
        else:  # num_rules_matched == 0
            return ClassificationStatus.UNCLASSIFIED
