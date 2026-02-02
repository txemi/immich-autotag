"""
protocol.py

Protocol definition for performance phase tracking.
Defines the interface for objects that can track performance phases.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class PerfPhaseTracker(Protocol):
    """Protocol for objects with a 'mark' method to track performance phases."""

    def mark(self, phase: str, event: str) -> None:
        """Mark the start or end of a performance phase.

        Args:
            phase: The name of the performance phase (e.g., 'lazy', 'full', 'assets')
            event: Either 'start' or 'end' to mark the beginning or end of the phase
        """
        ...
