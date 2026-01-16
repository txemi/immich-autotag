"""
Album Policy Resolver

Resolves which user groups should have access to an album based on:
1. Album name keyword matching
2. Configured selection rules
3. User group definitions

SYNCHRONIZATION POLICY (IMPORTANT):
- Configuration is the source of truth for album permissions
- Phase 1: Detection & logging only (no API calls)
- Phase 2: Complete synchronization - only configured members will have access
  * Members in config but not in album → ADDED
  * Members in album but not in config → REMOVED
  * This prevents accidental orphaned permissions when configuration changes

Admin users (system operators) should not appear in member lists to avoid accidental removal.
"""

import re
from typing import Dict, List, Optional

from immich_autotag.config.models import (
    AlbumSelectionRule,
    UserGroup,
)


class ResolvedAlbumPolicy:
    """Result of resolving an album's permission policy."""

    def __init__(
        self,
        album_name: str,
        album_id: str,
        matched_rules: List[str],
        groups: List[str],
        members: List[str],
        access_level: str,
    ):
        self.album_name = album_name
        self.album_id = album_id
        self.matched_rules = matched_rules  # Rule names that matched
        self.groups = groups  # Group names
        self.members = members  # Actual member emails
        self.access_level = access_level
        self.has_match = len(matched_rules) > 0

    def __str__(self) -> str:
        if not self.has_match:
            return f"Album '{self.album_name}': NO MATCH"
        return (
            f"Album '{self.album_name}': "
            f"Matched rules={self.matched_rules}, "
            f"Groups={self.groups}, "
            f"Members={self.members}, "
            f"Access={self.access_level}"
        )


def _split_album_name_to_words(album_name: str) -> List[str]:
    """
    Split album name by common separators into words.
    Separators: space, hyphen, underscore, dot
    Returns list of words (lowercase for matching)
    """
    # Replace separators with spaces, then split
    name_normalized = re.sub(r"[-_\.\s]+", " ", album_name)
    words = name_normalized.split()
    return [w.lower() for w in words]


def _match_keyword_in_album(album_name: str, keyword: str) -> bool:
    """
    Check if keyword appears in album name.
    Uses case-insensitive word matching (not substring).

    Example:
        album_name="2024-Familia-Vacation"
        keyword="familia"
        → Split to ["2024", "familia", "vacation"]
        → Match "familia" (case-insensitive)
        → True

        album_name="Family-Photo-Album"
        keyword="familia"
        → Split to ["family", "photo", "album"]
        → No match
        → False
    """
    words = _split_album_name_to_words(album_name)
    keyword_lower = keyword.lower()
    return keyword_lower in words


def resolve_album_policy(
    album_name: str,
    album_id: str,
    user_groups: Dict[str, UserGroup],
    selection_rules: List[AlbumSelectionRule],
) -> "ResolvedAlbumPolicy":
    """
    Resolve album permission policy based on config rules and user groups.

    This function determines which members (from configured groups) should have access
    to a given album based on keyword matching. The result is used for:

    - Phase 1: Reporting what permissions would be applied (dry-run)
    - Phase 2: Synchronizing actual permissions - ONLY members in resolved_policy.members
      will have access. Members not in this list will be removed to maintain sync.

    Args:
        album_name: Album name to match against rules
        album_id: Album ID
        user_groups: Dict mapping group name → UserGroup object
        selection_rules: List of AlbumSelectionRule to match

    Returns:
        ResolvedAlbumPolicy with resolved members (source of truth for Phase 2 sync)

    Example:
        Config has: grupo="familia" with ["abuelo@ex.com", "madre@ex.com"]
        Album is: "2024-Familia-Vacation"
        Result: ResolvedAlbumPolicy with members=["abuelo@ex.com", "madre@ex.com"]

        If later config removes "abuelo@ex.com", Phase 2 will automatically remove
        that user's access on next run (complete synchronization).
    """
    matched_rules_names: List[str] = []
    all_groups: List[str] = []
    all_members: List[str] = []
    access_level = "view"  # Default

    # Iterate rules and accumulate all matches
    for rule in selection_rules:
        if _match_keyword_in_album(album_name, rule.keyword):
            matched_rules_names.append(rule.name)
            all_groups.extend(rule.groups)
            access_level = rule.access  # Use last matched rule's access level

    # Resolve members from groups
    all_groups_unique = list(set(all_groups))  # Remove duplicates
    for group_name in all_groups_unique:
        if group_name in user_groups:
            group = user_groups[group_name]
            all_members.extend(group.members)

    # Remove duplicate members
    all_members_unique = list(set(all_members))

    return ResolvedAlbumPolicy(
        album_name=album_name,
        album_id=album_id,
        matched_rules=matched_rules_names,
        groups=all_groups_unique,
        members=all_members_unique,
        access_level=access_level,
    )


def build_user_groups_dict(
    user_groups: Optional[List[UserGroup]],
) -> Dict[str, UserGroup]:
    """
    Build a dict mapping group name → UserGroup for fast lookup.
    """
    if not user_groups:
        return {}
    return {group.name: group for group in user_groups}
