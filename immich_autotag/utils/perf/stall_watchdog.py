from __future__ import annotations

import datetime
import faulthandler
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.run_output.manager import RunOutputManager
from immich_autotag.statistics.statistics_manager import StatisticsManager


@dataclass(frozen=True)
class StallWatchdogHeartbeat:
    timestamp_monotonic: float
    phase: str
    detail: str | None
    processed_count: int | None
    last_processed_id: str | None


_heartbeat_lock = threading.RLock()
_heartbeat: StallWatchdogHeartbeat | None = None


def report_progress_heartbeat(
    *,
    phase: str,
    detail: str | None = None,
    processed_count: int | None = None,
    last_processed_id: str | None = None,
) -> None:
    global _heartbeat

    with _heartbeat_lock:
        _heartbeat = StallWatchdogHeartbeat(
            timestamp_monotonic=time.monotonic(),
            phase=phase,
            detail=detail,
            processed_count=processed_count,
            last_processed_id=last_processed_id,
        )


def _get_heartbeat() -> StallWatchdogHeartbeat | None:
    with _heartbeat_lock:
        return _heartbeat


def _build_dump_path() -> Path:
    run_exec = RunOutputManager.current().get_run_output_dir()
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    pid = (
        run_exec.path.name.split("_PID")[-1]
        if "_PID" in run_exec.path.name
        else "unknown"
    )
    return run_exec.get_custom_path(f"thread_dump_stall_{ts}_PID{pid}.txt")


def _write_thread_dump(
    *,
    reason: str,
    count: int,
    last_processed_id: str | None,
    heartbeat: StallWatchdogHeartbeat | None,
) -> Path:
    dump_path = _build_dump_path()
    now = datetime.datetime.now().isoformat()
    with dump_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n\n=== STALL WATCHDOG THREAD DUMP ===\n"
            f"timestamp={now}\n"
            f"reason={reason}\n"
            f"count={count}\n"
            f"last_processed_id={last_processed_id}\n"
            f"heartbeat_phase={heartbeat.phase if heartbeat else None}\n"
            f"heartbeat_detail={heartbeat.detail if heartbeat else None}\n"
            f"heartbeat_processed_count={heartbeat.processed_count if heartbeat else None}\n"
            f"heartbeat_last_processed_id={heartbeat.last_processed_id if heartbeat else None}\n"
            "===============================\n"
        )
        faulthandler.dump_traceback(file=handle, all_threads=True)
    return dump_path


def setup_stall_watchdog(
    *,
    enabled: bool,
    check_interval_seconds: float,
    stall_threshold_seconds: float,
    dump_cooldown_seconds: float,
) -> None:
    if not enabled:
        return

    if check_interval_seconds <= 0 or stall_threshold_seconds <= 0:
        log(
            "[WATCHDOG] Invalid configuration. Watchdog disabled.",
            level=LogLevel.WARNING,
        )
        return

    stop_event = threading.Event()

    def _watchdog_loop() -> None:
        stats_manager = StatisticsManager.get_instance()
        stats = stats_manager.get_or_create_run_stats()
        last_dump_ts = 0.0

        report_progress_heartbeat(
            phase="startup",
            detail="watchdog_initialized",
            processed_count=stats.count,
            last_processed_id=stats.last_processed_id,
        )

        log(
            (
                "[WATCHDOG] Stall watchdog enabled "
                f"(threshold={stall_threshold_seconds:.1f}s, "
                f"check_interval={check_interval_seconds:.1f}s)."
            ),
            level=LogLevel.PROGRESS,
        )

        while not stop_event.is_set():
            time.sleep(check_interval_seconds)

            try:
                current_stats = stats_manager.get_or_create_run_stats()
                current_count = current_stats.count
                current_last_processed_id = current_stats.last_processed_id
                now_ts = time.monotonic()
                heartbeat = _get_heartbeat()
                if heartbeat is None:
                    continue

                stalled_for = now_ts - heartbeat.timestamp_monotonic
                cooldown_elapsed = now_ts - last_dump_ts
                if (
                    stalled_for >= stall_threshold_seconds
                    and cooldown_elapsed >= dump_cooldown_seconds
                ):
                    dump_path = _write_thread_dump(
                        reason=f"heartbeat_not_moving_for_{stalled_for:.1f}s",
                        count=current_count,
                        last_processed_id=current_last_processed_id,
                        heartbeat=heartbeat,
                    )
                    last_dump_ts = now_ts
                    log(
                        (
                            "[WATCHDOG] Detected stalled processing. "
                            f"count={current_count}, "
                            f"last_processed_id={current_last_processed_id}. "
                            f"heartbeat_phase={heartbeat.phase}, "
                            f"heartbeat_detail={heartbeat.detail}. "
                            f"Thread dump written to: {dump_path}"
                        ),
                        level=LogLevel.IMPORTANT,
                    )
            except Exception as e:
                log(
                    f"[WATCHDOG] Error in stall watchdog loop: {e}",
                    level=LogLevel.WARNING,
                )

    thread = threading.Thread(
        target=_watchdog_loop,
        daemon=True,
        name="immich-autotag-stall-watchdog",
    )
    thread.start()
