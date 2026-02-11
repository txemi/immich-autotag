"""
ModificationEntriesList: encapsulates a list of ModificationEntry objects
with convenient query and aggregate methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, List

import attrs

if TYPE_CHECKING:
    from immich_autotag.report.modification_entry import ModificationEntry
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.albums.deduplicate_albums import deduplicate_albums_by_id
from immich_autotag.assets.deduplicate_assets import deduplicate_assets_by_id
from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult


@attrs.define(auto_attribs=True, slots=True, frozen=False)
class ModificationEntriesList(ProcessStepResult):

    """
    Encapsulates a list of ModificationEntry objects, providing convenient
    methods for querying, filtering, and aggregating modification data.
    Implements ProcessStepResult protocol for uniform interface with other result types.

    Access to entries should be through public methods only.
    """

    _entries: list[ModificationEntry] | None = attrs.field(
        default=attrs.Factory(list),
        repr=lambda entries: f"modifications={len(entries)}"
    )
    def __attrs_post_init__(self):
        if self._entries is None:
            self._entries = []
    def _get_entries_or_raise(self) -> list["ModificationEntry"]:
        if not self._entries or len(self._entries) == 0:
            raise ValueError("No modification entries available.")
        return self._entries

    def _count_entries_of_kind(self, entries: list["ModificationEntry"], kind: "ModificationKind") -> int:
        """Returns the count of entries of a given kind in the provided entries list."""
        return sum(1 for entry in entries if entry.kind == kind)

    def _count_map_by_kind(self, entries: list["ModificationEntry"]) -> dict["ModificationKind", int]:
        """Returns a dict mapping each kind to its count in the provided entries list."""
        kinds = {entry.kind for entry in entries}
        return {kind: self._count_entries_of_kind(entries, kind) for kind in kinds}

    def entries(self) -> list[ModificationEntry]:
        """Returns a copy of the underlying list of entries. Raises if empty."""
        return list(self._get_entries_or_raise())

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

    def get_events(self) -> ModificationEntriesList:
        """Returns all modification entries (events) from this result."""
        return self

    def has_entries_of_kind(self, kind: ModificationKind) -> bool:
        """Returns True if list contains entries of the specified kind."""
        return any(entry.kind == kind for entry in self._entries)

    def filter_by_kind(self, kind: ModificationKind) -> ModificationEntriesList:
        """Returns a new list containing only entries of the specified kind."""
        filtered = [entry for entry in self._entries if entry.kind == kind]
        return ModificationEntriesList(entries=filtered)

    def count_by_kind(self, kind: ModificationKind) -> int:
        """Returns the count of entries with the specified kind."""
        return sum(1 for entry in self._entries if entry.kind == kind)

    def get_all_kinds(self) -> set[ModificationKind]:
        """Returns a set of all ModificationKind values present in the list."""
        return {entry.kind for entry in self._entries}

    def extend(self, other: ModificationEntriesList) -> ModificationEntriesList:
        """Returns a new list with entries from both lists."""
        combined = self._entries + other.entries()
        return ModificationEntriesList(entries=combined)

    def append(self, entry: ModificationEntry) -> None:
        """Adds the entry to the internal list (in-place)."""
        self._entries.append(entry)

    def to_list(self) -> list[ModificationEntry]:
        """Returns the underlying list of entries. Raises if empty."""
        return list(self._get_entries_or_raise())

    def format(self) -> str:
        """
        Format the modification entries list as a summary string.

        Shows the total count and breakdown by modification kind.

        Returns:
            A formatted string with total modifications and counts by kind.
            Example: "5 modifications (added=2, removed=3)"
        """
        entries = self._get_entries_or_raise()
        total = len(entries)

        # Get all kinds and their counts
        kind_counts = self._count_map_by_kind(entries)

        # Sort kinds by name for consistent output
        sorted_kinds = sorted(kind_counts.keys(), key=lambda k: str(k))

        # Build breakdown string
        breakdown = ", ".join(
            f"{kind.name}={count}"
            for kind, count in zip(sorted_kinds, [kind_counts[k] for k in sorted_kinds])
        )

        word = "modification" if total == 1 else "modifications"
        return f"{total} {word} ({breakdown})"

    def get_albums(self) -> list[AlbumResponseWrapper]:
        """
        Returns a deduplicated list of all albums referenced by the modifications, using album uuid for uniqueness.
        Raises if no entries are present.
        """
        entries = self._get_entries_or_raise()
        albums: list[AlbumResponseWrapper] = [
            entry.album for entry in entries if entry.album is not None
        ]
        return deduplicate_albums_by_id(albums)

    def get_assets(self) -> list[AssetResponseWrapper]:
        """
        Returns a deduplicated list of all asset wrappers referenced by the modifications, using asset id for uniqueness.
        Raises if no entries are present.
        """
        entries = self._get_entries_or_raise()
        assets: list[AssetResponseWrapper] = [
            entry.asset_wrapper
            for entry in entries
            if entry.asset_wrapper is not None
        ]
        return deduplicate_assets_by_id(assets)

    def count_albums(self) -> int:
        """Returns the number of unique albums referenced by the modifications. Raises if no entries are present."""
        return len(self.get_albums())

    def count_assets(self) -> int:
        """Returns the number of unique assets referenced by the modifications. Raises if no entries are present."""
        return len(self.get_assets())

    @staticmethod
    def combine_optional(
        first: ModificationEntriesList | None, second: ModificationEntriesList | None
    ) -> ModificationEntriesList | None:
        if first and second:
            combined = first + second
            return combined if combined.entries() else None
        elif first and first.entries():
            return first
        elif second and second.entries():
            return second
        return None

    def format_first_entry_kind(self) -> str:
        """
        Returns a summary string for the modifications using the class's format() method.
        """
        return self.format()

    def count_changes(self) -> int:
        """
        Returns the number of entries that represent a change (modification). Raises if no entries are present.
        Considera como cambio cualquier entrada cuyo kind no sea INFO ni NO_OP.
        """
        entries = self._get_entries_or_raise()
        return sum(
            1
            for entry in entries
            if entry.kind.is_change()
        )

    def __getitem__(self, index: int) -> ModificationEntry:
        """Allows index access to entries (list-like). Raises if empty."""
        return self._get_entries_or_raise()[index]

    def __iter__(self) -> Iterator[ModificationEntry]:
        """Allows iteration over entries. Raises if empty."""
        return iter(self._get_entries_or_raise())

    def __len__(self) -> int:
        """Returns the number of entries in the list. Raises if empty."""
        return len(self._get_entries_or_raise())

    def __add__(self, other: ModificationEntriesList) -> ModificationEntriesList:
        if not isinstance(other, ModificationEntriesList):
            raise TypeError(
                "Can only add ModificationEntriesList to ModificationEntriesList"
            )
        combined_entries = self.entries() + other.entries()
        return ModificationEntriesList(entries=combined_entries)

    def __bool__(self) -> bool:
        """Returns True if list has any entries. Raises if empty."""
        return len(self._get_entries_or_raise()) > 0
