"""
ModificationEntriesList: encapsulates a list of ModificationEntry objects
with convenient query and aggregate methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

import attrs

if TYPE_CHECKING:
    from immich_autotag.report.modification_entry import ModificationEntry
    from immich_autotag.report.modification_kind import ModificationKind


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ModificationEntriesList:
    """
    Encapsulates a list of ModificationEntry objects, providing convenient
    methods for querying, filtering, and aggregating modification data.
    Implements ProcessStepResult protocol for uniform interface with other result types.

    Access to entries should be through public methods only.
    The 'entries' attribute is internal and exposed via iteration/to_list() only.
    """

    entries: list["ModificationEntry"] = attrs.field(
        default=attrs.Factory(list), repr=False
    )

    def has_changes(self) -> bool:
        """Returns True if list contains any modification entries."""
        return len(self.entries) > 0

    def has_errors(self) -> bool:
        """Returns True if list contains any ERROR or WARNING modification entries."""
        return any(
            entry.kind.is_error() or entry.kind.is_warning() for entry in self.entries
        )

    def has_entries_of_kind(self, kind: "ModificationKind") -> bool:
        """Returns True if list contains entries of the specified kind."""
        return any(entry.kind == kind for entry in self.entries)

    def filter_by_kind(self, kind: "ModificationKind") -> "ModificationEntriesList":
        """Returns a new list containing only entries of the specified kind."""
        filtered = [entry for entry in self.entries if entry.kind == kind]
        return ModificationEntriesList(entries=filtered)

    def count_by_kind(self, kind: "ModificationKind") -> int:
        """Returns the count of entries with the specified kind."""
        return sum(1 for entry in self.entries if entry.kind == kind)

    def get_all_kinds(self) -> set["ModificationKind"]:
        """Returns a set of all ModificationKind values present in the list."""
        return {entry.kind for entry in self.entries}

    def extend(self, other: "ModificationEntriesList") -> "ModificationEntriesList":
        """Returns a new list with entries from both lists."""
        if isinstance(other, ModificationEntriesList):
            combined = self.entries + other.entries
        else:
            combined = self.entries + list(other)
        return ModificationEntriesList(entries=combined)

    def append(self, entry: "ModificationEntry") -> "ModificationEntriesList":
        """Returns a new list with the entry appended."""
        new_entries = self.entries + [entry]
        return ModificationEntriesList(entries=new_entries)

    def to_list(self) -> list["ModificationEntry"]:
        """Returns the underlying list of entries."""
        return list(self.entries)

    def __iter__(self) -> Iterator["ModificationEntry"]:
        """Allows iteration over entries."""
        return iter(self.entries)

    def __len__(self) -> int:
        """Returns the number of entries in the list."""
        return len(self.entries)

    def __bool__(self) -> bool:
        """Returns True if list has any entries."""
        return len(self.entries) > 0
