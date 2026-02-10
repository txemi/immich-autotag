"""
ModificationEntriesList: encapsulates a list of ModificationEntry objects
with convenient query and aggregate methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, List, Set

import attrs

if TYPE_CHECKING:
    from immich_autotag.report.modification_entry import ModificationEntry
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ModificationEntriesList(ProcessStepResult):
    """
    Encapsulates a list of ModificationEntry objects, providing convenient
    methods for querying, filtering, and aggregating modification data.
    Implements ProcessStepResult protocol for uniform interface with other result types.

    Access to entries should be through public methods only.
    """

    _entries: List["ModificationEntry"] = attrs.field(
        default=attrs.Factory(list),
        repr=lambda entries: f"modifications={len(entries)}",
        alias="entries",
    )

    def entries(self) -> List["ModificationEntry"]:
        """Returns a copy of the underlying list of entries."""
        return list(self._entries)

    def has_changes(self) -> bool:
        """Returns True if list contains any modification entries."""
        return len(self._entries) > 0

    def has_errors(self) -> bool:
        """Returns True if list contains any ERROR or WARNING modification entries."""
        return any(
            entry.kind.is_error() or entry.kind.is_warning() for entry in self._entries
        )

    def get_title(self) -> str:
        return "Rule engine modifications"

    def get_events(self) -> "ModificationEntriesList":
        """Returns all modification entries (events) from this result."""
        return self

    def has_entries_of_kind(self, kind: "ModificationKind") -> bool:
        """Returns True if list contains entries of the specified kind."""
        return any(entry.kind == kind for entry in self._entries)

    def filter_by_kind(self, kind: "ModificationKind") -> "ModificationEntriesList":
        """Returns a new list containing only entries of the specified kind."""
        filtered = [entry for entry in self._entries if entry.kind == kind]
        return ModificationEntriesList(entries=filtered)

    def count_by_kind(self, kind: "ModificationKind") -> int:
        """Returns the count of entries with the specified kind."""
        return sum(1 for entry in self._entries if entry.kind == kind)

    def get_all_kinds(self) -> set["ModificationKind"]:
        """Returns a set of all ModificationKind values present in the list."""
        return {entry.kind for entry in self._entries}

    def extend(self, other: "ModificationEntriesList") -> "ModificationEntriesList":
        """Returns a new list with entries from both lists."""
        combined = self._entries + other.entries()
        return ModificationEntriesList(entries=combined)

    def append(self, entry: "ModificationEntry") -> "ModificationEntriesList":
        """Returns a new list with the entry appended."""
        new_entries = self._entries + [entry]
        return ModificationEntriesList(entries=new_entries)

    def to_list(self) -> list["ModificationEntry"]:
        """Returns the underlying list of entries."""
        return list(self._entries)

    def format(self) -> str:
        """
        Format the modification entries list as a summary string.

        Shows the total count and breakdown by modification kind.

        Returns:
            A formatted string with total modifications and counts by kind.
            Example: "5 modifications (added=2, removed=3)"
        """
        total = len(self._entries)

        if total == 0:
            return "No modifications"

        # Get all kinds and their counts
        kinds = self.get_all_kinds()
        kind_counts = {kind: self.count_by_kind(kind) for kind in kinds}

        # Sort kinds by name for consistent output
        sorted_kinds = sorted(kind_counts.keys(), key=lambda k: str(k))

        # Build breakdown string
        breakdown = ", ".join(
            f"{kind.name}={count}"
            for kind, count in zip(sorted_kinds, [kind_counts[k] for k in sorted_kinds])
        )

        word = "modification" if total == 1 else "modifications"
        return f"{total} {word} ({breakdown})"

    def get_albums(self) -> Set["AlbumResponseWrapper"]:
        """
        Returns a set of all albums referenced by the modifications.
        """
        return {entry.album for entry in self._entries if entry.album is not None}

    def get_assets(self) -> Set["AssetResponseWrapper"]:
        """
        Returns a set of all asset wrappers referenced by the modifications.
        Assumes all entries are ModificationEntry and have asset_wrapper attribute.
        """
        return {
            entry.asset_wrapper
            for entry in self._entries
            if entry.asset_wrapper is not None
        }

    def count_albums(self) -> int:
        """Returns the number of unique albums referenced by the modifications."""
        return len(self.get_albums())

    def count_assets(self) -> int:
        """Returns the number of unique assets referenced by the modifications."""
        return len(self.get_assets())

    def __getitem__(self, index: int) -> "ModificationEntry":
        """Allows index access to entries (list-like)."""
        return self._entries[index]

    def __iter__(self) -> Iterator["ModificationEntry"]:
        """Allows iteration over entries."""
        return iter(self._entries)

    def __len__(self) -> int:
        """Returns the number of entries in the list."""
        return len(self._entries)

    def __bool__(self) -> bool:
        """Returns True if list has any entries."""
        return len(self._entries) > 0
