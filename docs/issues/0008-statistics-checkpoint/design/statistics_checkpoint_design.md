# Design: Statistics and Checkpoint Management for Immich-Autotag

## Context

The application processes a large number of assets and may take a long time to complete. It needs to:
- Track progress and statistics during execution.
- Allow resuming from a checkpoint if interrupted.
- Provide structured, historical logs of each run for later analysis.

## Goals

1. **Evolve the Checkpoint System:**
   - The current checkpoint system (read/write/delete) will be expanded to record more execution data.
   - The new system will be a superset: it will keep the old checkpoint data and add counters/statistics.

2. **Structured, Persistent Logging:**
   - Use a structured file format (YAML preferred) instead of a simple CSV line.
   - Map the file to a Python class (preferably using pydantic for validation/serialization).
   - Store the file in the `logs/` directory, with the filename including the execution start date/time.
   - The file will include:
     - Start and end timestamps
     - Number of assets processed
     - (Future) Per-tag asset counters
     - Any other relevant statistics

3. **File Management and Logic:**
   - On startup, the system will look for the most recent statistics file in `logs/`.
   - If the file's end date is not null, the previous run finished and a new file will be created.
   - The statistics manager class will encapsulate this logic.

4. **Extensibility:**
   - The statistics class will provide methods to increment counters, set variables, etc.
   - Old checkpoint calls will be adapted to use the new class.
   - The statistics file will not be deleted at the end, but kept as a historical record.

5. **Progress Reporting (Future):**
   - The statistics class will be able to inform the user of progress (e.g., percentage complete).
   - Eventually, it will delegate to a dedicated progress reporter class, simplifying the main flow.

## Implementation Plan

- Create a new statistics data class (pydantic or attrs) for YAML serialization.
- Create a manager class for reading/writing/updating the statistics file.
- Refactor checkpoint logic to use the new manager.
- Add extensible methods for updating statistics.
- Ensure all files are written to `logs/` with timestamped filenames.
- Document the structure and usage for future reference.

---

This document serves as a reference for the design and rationale behind the new statistics and checkpoint management system. Update as the implementation evolves.
