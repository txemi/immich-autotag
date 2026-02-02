from typing import Protocol


class ProcessStepResult(Protocol):
    """
    Protocol that defines the interface for all processing step results.
    Any result object must implement these two methods to be used uniformly
    in AssetProcessReport.
    """

    def has_changes(self) -> bool:
        """Returns True if this step resulted in changes to the asset."""
        ...

    def has_errors(self) -> bool:
        """Returns True if this step encountered errors during processing."""
        ...
