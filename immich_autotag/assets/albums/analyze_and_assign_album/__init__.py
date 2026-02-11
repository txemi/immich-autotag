"""Album assignment logic for assets based on their classification status.

This module orchestrates the complete album assignment workflow for classified,
conflicted, and unclassified assets.
"""

from __future__ import annotations

from .album_assignment_report import AlbumAssignmentReport
from .album_assignment_result import AlbumAssignmentResult

__all__ = [
    "AlbumAssignmentReport",
    "AlbumAssignmentResult",
]
