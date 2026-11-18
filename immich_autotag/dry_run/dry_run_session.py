"""
The dry run of this process: its transport, its journal and its summary.

ImmichClientWrapper starts it when it builds the client (start_for_current_run),
and the entrypoint finishes it at the end of the run, also when the run fails,
so the summary is always written.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import httpx

from immich_autotag.dry_run.change_journal import DryRunJournal, format_summary_lines
from immich_autotag.dry_run.dry_run_transport import DryRunTransport

_current: "DryRunSession | None" = None


class DryRunSession:
    def __init__(self, *, transport: DryRunTransport) -> None:
        self._transport = transport
        self._summary: dict[str, Any] | None = None

    @staticmethod
    def start(
        *,
        base_url: str,
        changes_path: Path,
        summary_path: Path,
        is_temporary_album: Callable[[str], bool] | None = None,
        inner: httpx.BaseTransport | None = None,
    ) -> "DryRunSession":
        global _current
        if _current is not None:
            raise RuntimeError("A dry-run session is already running in this process.")
        journal = DryRunJournal(
            changes_path=changes_path,
            summary_path=summary_path,
            is_temporary_album=is_temporary_album,
        )
        transport = DryRunTransport(
            inner=inner if inner is not None else httpx.HTTPTransport(),
            base_path=httpx.URL(base_url).path,
            journal=journal,
        )
        _current = DryRunSession(transport=transport)
        return _current

    @staticmethod
    def get_current() -> "DryRunSession | None":
        return _current

    @staticmethod
    def reset() -> None:
        """Forgets the current session. Meant for tests."""
        global _current
        if _current is not None:
            _current.get_journal().close()
        _current = None

    def get_transport(self) -> DryRunTransport:
        return self._transport

    def get_journal(self) -> DryRunJournal:
        return self._transport.get_journal()

    def finish(
        self,
        *,
        completed: bool,
        modification_counts: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Writes the summary (once) and prints it."""
        if self._summary is not None:
            return self._summary
        journal = self.get_journal()
        summary = journal.write_summary(
            completed=completed, modification_counts=modification_counts
        )
        journal.close()
        for line in format_summary_lines(summary):
            print(line)
        print(f"[DRY-RUN] Summary file: {journal.get_summary_path()}")
        self._summary = summary
        return summary


def start_for_current_run(base_url: str) -> DryRunSession:
    """Starts the dry run of this process, writing into the current run folder."""
    from immich_autotag.assets.albums.temporary_manager.naming import (
        is_temporary_album,
    )
    from immich_autotag.run_output.manager import RunOutputManager

    run_dir = RunOutputManager.current().get_run_output_dir()
    return DryRunSession.start(
        base_url=base_url,
        changes_path=run_dir.get_dry_run_changes_path(),
        summary_path=run_dir.get_dry_run_summary_path(),
        is_temporary_album=is_temporary_album,
    )


def finish_current_session(*, completed: bool) -> dict[str, Any] | None:
    """Finishes the dry run of this process, if there is one."""
    session = DryRunSession.get_current()
    if session is None:
        return None
    counts: dict[str, int] = {}
    try:
        from immich_autotag.report.modification_report import ModificationReport

        report = ModificationReport.get_instance()
        counts = {
            kind.name: count for kind, count in report.get_entry_type_counts().items()
        }
    except Exception as error:  # the summary must be written even so
        print(f"[DRY-RUN] Could not read the modification report counts: {error}")
    return session.finish(completed=completed, modification_counts=counts)
