from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from immich_autotag.report.modification_entries_list import ModificationEntriesList


class ProcessStepResult(Protocol):
    """
    Protocol that defines the interface for all processing step results.
    Any result object must implement these methods to be used uniformly
    in AssetProcessReport.

    This protocol enables symmetric treatment of different result types,
    allowing them to be stored in collections and processed uniformly.
    """

    def has_changes(self) -> bool:
        """Returns True if this step resulted in changes to the asset."""
        ...

    def has_errors(self) -> bool:
        """Returns True if this step encountered errors during processing."""
        ...

    def get_title(self) -> str:
        """Returns the display title for this processing step."""
        ...

    def get_events(self) -> "ModificationEntriesList":
        """
        Returns all events/entries from this processing step.

        Events represent all changes, warnings, and errors that occurred
        during processing. They are unified as ModificationEntry objects
        that can be queried and reported uniformly across all step results.

        Returns:
            A ModificationEntriesList containing all events from this step,
            or empty list if no events occurred.
        """
        ...

    def format(self) -> str:
        """
        Format the result as a human-readable string for display.

        Returns:
            A formatted string describing the processing step result,
            suitable for display to users or in logs.
        """
        ...
