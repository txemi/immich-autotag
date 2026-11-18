"""
Record of every change a dry run would have made, plus its counts.

Each intercepted write becomes one JSON line in the changes file (JSONL), written
as soon as it happens, so an interrupted run still leaves what it saw. The
summary (JSON) holds the counts: how many assets would go into temporary
albums, how many asset dates would change, and so on.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any, Callable

from immich_autotag.dry_run.request_classifier import WriteOperation


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class _OperationCount:
    __slots__ = ("calls", "items")

    def __init__(self) -> None:
        self.calls = 0
        self.items = 0


class DryRunJournal:
    """Writes the changes file and keeps the counters of the summary."""

    def __init__(
        self,
        *,
        changes_path: Path,
        summary_path: Path,
        is_temporary_album: Callable[[str], bool] | None = None,
    ) -> None:
        self._changes_path = changes_path
        self._summary_path = summary_path
        self._is_temporary_album = is_temporary_album
        self._started_at = _now_iso()
        self._sequence = 0
        self._handle: IO[str] | None = None
        self._reads_forwarded = 0
        self._reads_answered_locally = 0
        self._operations: dict[str, _OperationCount] = {}
        self._temp_albums_created = 0
        self._temp_assets_added = 0
        self._temp_assets_removed = 0
        self._temp_distinct_added: set[str] = set()
        self._date_updates = 0
        self._date_distinct_assets: set[str] = set()
        self._simulated_ids: list[str] = []
        self._unknown_writes: list[str] = []

    def get_changes_path(self) -> Path:
        return self._changes_path

    def get_summary_path(self) -> Path:
        return self._summary_path

    def is_temporary_album_name(self, album_name: str | None) -> bool | None:
        if album_name is None or self._is_temporary_album is None:
            return None
        return bool(self._is_temporary_album(album_name))

    # --- reads --------------------------------------------------------------

    def count_forwarded_read(self) -> None:
        self._reads_forwarded += 1

    def count_local_read(self) -> None:
        self._reads_answered_locally += 1

    def _update_counters(
        self,
        operation: WriteOperation,
        method: str,
        path: str,
        target: dict[str, Any],
        asset_ids: list[str],
    ) -> None:
        count = self._operations.setdefault(operation.value, _OperationCount())
        count.calls += 1
        count.items += len(asset_ids)
        temporary = target.get("temporary_album") is True
        if operation is WriteOperation.CREATE_ALBUM and temporary:
            self._temp_albums_created += 1
        elif operation is WriteOperation.ADD_ASSETS_TO_ALBUM and temporary:
            self._temp_assets_added += len(asset_ids)
            self._temp_distinct_added.update(asset_ids)
        elif operation is WriteOperation.REMOVE_ASSETS_FROM_ALBUM and temporary:
            self._temp_assets_removed += len(asset_ids)
        elif operation is WriteOperation.UPDATE_ASSET and target.get("changes_date"):
            self._date_updates += 1
            self._date_distinct_assets.update(asset_ids)
        elif operation is WriteOperation.UNKNOWN:
            self._unknown_writes.append(f"{method} {path}")

    def _write_line(self, entry: dict[str, Any]) -> None:
        if self._handle is None:
            self._changes_path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = open(self._changes_path, "a", encoding="utf-8")
        self._handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        self._handle.flush()

    # --- writes -------------------------------------------------------------

    def record_write(
        self,
        *,
        operation: WriteOperation,
        method: str,
        path: str,
        target: dict[str, Any],
        asset_ids: list[str],
        body: Any,
        simulated_status: int,
        simulated_ids: list[str],
    ) -> dict[str, Any]:
        """Appends one change to the changes file and updates the counters."""
        self._sequence += 1
        entry: dict[str, Any] = {
            "seq": self._sequence,
            "at": _now_iso(),
            "operation": operation.value,
            "method": method,
            "path": path,
            "target": target,
            "asset_count": len(asset_ids),
            "asset_ids": asset_ids,
            "body": body,
            "sent_to_immich": False,
            "simulated_status": simulated_status,
            "simulated_ids": simulated_ids,
        }
        self._update_counters(operation, method, path, target, asset_ids)
        self._simulated_ids.extend(simulated_ids)
        self._write_line(entry)
        return entry

    # --- summary ------------------------------------------------------------

    def build_summary(
        self,
        *,
        completed: bool,
        modification_counts: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        operations = {
            name: {"calls": count.calls, "assets": count.items}
            for name, count in sorted(self._operations.items())
        }
        writes = sum(count.calls for count in self._operations.values())
        return {
            "dry_run": True,
            "completed": completed,
            "started_at": self._started_at,
            "finished_at": _now_iso(),
            "changes_file": str(self._changes_path),
            "requests": {
                "reads_sent_to_immich": self._reads_forwarded,
                "reads_answered_by_simulation": self._reads_answered_locally,
                "writes_intercepted": writes,
                "writes_sent_to_immich": 0,
            },
            "operations": operations,
            "temporary_albums": {
                "albums_created": self._temp_albums_created,
                "asset_additions": self._temp_assets_added,
                "distinct_assets_added": len(self._temp_distinct_added),
                "asset_removals": self._temp_assets_removed,
            },
            "asset_dates": {
                "updates": self._date_updates,
                "distinct_assets": len(self._date_distinct_assets),
            },
            "simulated_ids": list(self._simulated_ids),
            "unknown_writes": list(self._unknown_writes),
            "modification_report_counts": dict(
                sorted((modification_counts or {}).items())
            ),
        }

    def write_summary(
        self,
        *,
        completed: bool,
        modification_counts: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        summary = self.build_summary(
            completed=completed, modification_counts=modification_counts
        )
        self._summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._summary_path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return summary

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


def format_summary_lines(summary: dict[str, Any]) -> list[str]:
    """Human-readable lines for the console at the end of a dry run."""
    requests = summary["requests"]
    temp = summary["temporary_albums"]
    dates = summary["asset_dates"]
    lines = [
        "[DRY-RUN] Nothing was written to Immich.",
        f"[DRY-RUN] Writes intercepted: {requests['writes_intercepted']} "
        f"(reads sent: {requests['reads_sent_to_immich']}, "
        f"answered by the simulation: {requests['reads_answered_by_simulation']})",
        f"[DRY-RUN] Temporary albums: {temp['albums_created']} would be created, "
        f"{temp['distinct_assets_added']} distinct assets would be added "
        f"({temp['asset_additions']} additions), "
        f"{temp['asset_removals']} removals",
        f"[DRY-RUN] Asset dates: {dates['distinct_assets']} assets would change "
        f"({dates['updates']} updates)",
    ]
    for name, count in summary["operations"].items():
        lines.append(
            f"[DRY-RUN]   {name}: {count['calls']} calls, {count['assets']} assets"
        )
    if summary["unknown_writes"]:
        lines.append(
            "[DRY-RUN] Writes with no simulation (not sent, answered with an "
            f"error): {len(summary['unknown_writes'])}"
        )
    lines.append(f"[DRY-RUN] Changes file: {summary['changes_file']}")
    return lines
