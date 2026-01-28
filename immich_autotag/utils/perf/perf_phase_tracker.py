"""
perf_phase_tracker.py

Allows recording start and end times of key phases (lazy load, full load,
asset process) and logging a summary at any time (including exceptions).
"""

import time
from typing import ClassVar, Dict, Optional

import attrs

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log


@attrs.define(slots=True, auto_attribs=True)
class PerfPhaseTracker:
    phases: Dict[str, Dict[str, Optional[float]]] = attrs.field(
        factory=lambda: {
            "lazy": {"start": None, "end": None},
            "full": {"start": None, "end": None},
            "assets": {"start": None, "end": None},
        }
    )

    _instance: ClassVar[Optional["PerfPhaseTracker"]] = None

    @classmethod
    def get_instance(cls) -> "PerfPhaseTracker":
        if cls._instance is None:
            cls._instance = PerfPhaseTracker()
        return cls._instance

    def reset(self) -> None:
        self.phases = {
            "lazy": {"start": None, "end": None},
            "full": {"start": None, "end": None},
            "assets": {"start": None, "end": None},
        }

    def mark(self, *, phase: str, event: str) -> None:
        assert phase in self.phases and event in ("start", "end")
        self.phases[phase][event] = time.time()

    def log_summary(self) -> None:
        for phase, times in self.phases.items():
            s, e = times["start"], times["end"]
            if s is not None and e is not None:
                elapsed = e - s
                log(f"[PERF] Phase '{phase}': {elapsed:.2f} s", level=LogLevel.PROGRESS)
            elif s is not None:
                log(
                    f"[PERF] Phase '{phase}': started at {s}, not finished",
                    level=LogLevel.PROGRESS,
                )


perf_phase_tracker = PerfPhaseTracker.get_instance()
