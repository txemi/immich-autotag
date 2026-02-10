from typing import TYPE_CHECKING, List, Optional

import attr

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult


@attr.s(auto_attribs=True, slots=True)
class AssetProcessStepResult:
    step_name: str
    changed: bool = False
    details: Optional[str] = None
    data: Optional[object] = None

    def __str__(self):
        return f"{self.step_name}: {'CHANGED' if self.changed else 'NO CHANGE'}" + (
            f" | {self.details}" if self.details else ""
        )


@attr.s(auto_attribs=True, slots=True)
class AssetProcessReport(ProcessStepResult):
    """
    Collects the results of each step in process_single_asset for a single asset.
    Aggregates all processing step results in a single unified list, maintaining
    the execution order of the processing pipeline.

    Implements ProcessStepResult protocol with has_changes(), has_errors(),
    get_title(), and format() methods.

    All result types are added to the internal results list via add_result() method
    in the order they are produced during asset processing. This maintains temporal
    consistency with the actual execution flow and enables symmetric handling of
    all results regardless of their specific type.

    Private Attributes:
        _process_step_results: List of ProcessStepResult objects in execution order
        _legacy_steps: Legacy step list for backward compatibility/debugging
    """

    asset_wrapper: "AssetResponseWrapper"
    _process_step_results: List[ProcessStepResult] = attr.ib(
        factory=lambda: [], repr=False
    )
    # Optionally, keep the old steps list for extensibility/debug
    _legacy_steps: List[AssetProcessStepResult] = attr.ib(
        factory=lambda: [], repr=False
    )

    def add_result(self, result: Optional[ProcessStepResult]) -> None:
        """
        Add a processing step result to the report in execution order.

        Args:
            result: A ProcessStepResult object (or None to skip)
        """
        if result is not None:
            self._process_step_results.append(result)

    def add_legacy_step(self, step: AssetProcessStepResult) -> None:
        """Add a legacy step for backward compatibility/debugging."""
        self._legacy_steps.append(step)

    def get_process_step_results(self) -> List[ProcessStepResult]:
        """Return a copy of the process step results list."""
        return list(self._process_step_results)

    def has_changes(self) -> bool:
        """Returns True if any processing step resulted in changes."""
        return any(result.has_changes() for result in self._process_step_results)

    def has_errors(self) -> bool:
        """Returns True if any processing step encountered errors."""
        return any(result.has_errors() for result in self._process_step_results)

    def _get_changes_details(self) -> str:
        """
        Generate a concise string describing what changes were made.

        Iterates through all results symmetrically using the ProcessStepResult protocol,
        calling format() on each to obtain uniform string representation.
        """
        changes: list[str] = []
        for result in self._process_step_results:
            changes.append(result.format())

        if changes:
            return " | ".join(changes)
        return ""

    def format(self) -> str:
        """Return a formatted string representation of the report."""
        changes_indicator = "✓ CHANGES" if self.has_changes() else "○ NO CHANGES"
        changes_details = self._get_changes_details()
        result = f"[ASSET REPORT] {changes_indicator}"
        if changes_details:
            result += f" | {changes_details}"
        return result

    def get_title(self) -> str:
        """Return the title for this report in ProcessStepResult protocol."""
        return "Asset process report"

    def get_events(self):
        """Returns all events from all processing step results aggregated."""
        from immich_autotag.report.modification_entries_list import (
            ModificationEntriesList,
        )

        aggregated = ModificationEntriesList()
        for result in self._process_step_results:
            events = result.get_events()
            aggregated = aggregated.extend(events)
        return aggregated

    def any_changes(self) -> bool:
        """Backward-compatible alias for has_changes()."""
        return self.has_changes()

    def summary(self) -> str:
        """Generate a comprehensive summary of the asset processing results."""
        lines: List[str] = []
        asset_url = self.asset_wrapper.get_immich_photo_url().geturl()

        # Build header with overall status
        changes_indicator = "✓ CHANGES" if self.has_changes() else "○ NO CHANGES"
        lines.append(f"[ASSET REPORT] {changes_indicator}")
        lines.append(f"  Asset: {asset_url}")

        # Add concise details line if there are changes
        changes_details = self._get_changes_details()
        if changes_details:
            lines.append(f"  Details: {changes_details}")

        # Add individual results for detailed info (symmetric iteration by execution order)
        if self._process_step_results:
            lines.append(f"  Processing steps ({len(self._process_step_results)}):")
            for idx, result in enumerate(self._process_step_results, 1):
                title = result.get_title()
                mod_marker = (
                    " [MODIFIED ✨]" if result.has_changes() else " [NO MODIFICATION]"
                )
                lines.append(f"    {idx:02d}. {title}: {result.format()}{mod_marker}")

        # Add a final summary line about modifications (in English)
        changed_steps = [
            f"{idx:02d}. {result.get_title()}"
            for idx, result in enumerate(self._process_step_results, 1)
            if result.has_changes()
        ]
        if changed_steps:
            lines.append(
                f"[SUMMARY] Modifications occurred in: {', '.join(changed_steps)}."
            )
        else:
            lines.append("[SUMMARY] No modifications occurred in any step.")
        return "\n".join(lines)

    def __str__(self):
        return self.summary()
