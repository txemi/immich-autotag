from __future__ import annotations

import time

from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def log_final_summary() -> None:
    from immich_autotag.statistics.statistics_manager import StatisticsManager

    stats = StatisticsManager.get_instance().get_stats()
    count = stats.count
    start_time = stats.get_start_time()
    total_time = time.time() - start_time

    # Get modification statistics
    tag_mod_report = ModificationReport.get_instance()
    total_modifications = len(tag_mod_report.modifications)

    # Build the complete report as a single string
    report_lines = [
        "═══════════════════════════════════════════════════════",
        "EXECUTION SUMMARY",
        "───────────────────────────────────────────────────────",
        f"Total assets processed: {count}",
        f"Total time: {total_time:.2f} s | Average per asset: {total_time/count if count else 0:.3f} s",
        "───────────────────────────────────────────────────────",
        "MODIFICATIONS DETECTED",
        "───────────────────────────────────────────────────────",
    ]

    if total_modifications == 0:
        report_lines.append("✓ NO CHANGES - All assets processed without modifications")
    else:
        report_lines.append(
            f"⚠ CHANGES DETECTED: {total_modifications} modification(s)"
        )
        # Add modification details
        for entry in tag_mod_report.modifications:
            serializable = entry.to_serializable()
            report_lines.append(f"  • {serializable.to_log_string()}")

    report_lines.append("═══════════════════════════════════════════════════════")

    # Print entire report in one call
    log("\n".join(report_lines), level=LogLevel.PROGRESS)

    # Flush report to file if needed
    if total_modifications > 0:
        tag_mod_report.flush()
    MIN_ASSETS = 0  # Change this value if you know the real minimum number of assets
    if count < MIN_ASSETS:
        raise Exception(
            f"ERROR: Unexpectedly low number of assets: {count} < {MIN_ASSETS}"
        )
