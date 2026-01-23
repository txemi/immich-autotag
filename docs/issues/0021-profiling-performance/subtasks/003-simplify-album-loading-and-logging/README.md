
# 003 - Simplify Album Loading and Logging

**Status:** Proposed
**Created:** 2026-01-23
**Parent Issue:** [0021-profiling-performance](../)

## Context & Motivation

We are currently experiencing performance issues in the main application flow, especially due to lazy loading of albums and assets. This complicates analysis and debugging, since the first time albums are accessed, a full load occurs that penalizes the first asset and can generate hard-to-track conditions (cycles, unexpected latencies, etc.).

The goal is to simplify the flow to release a stable and debuggable version. We want all albums to be fully loaded before iterating over assets, so the first asset does not bear the entire loading cost and lazy-loading problems do not mix with other bottlenecks.

## Objectives

1. **Simplify the flow:**
   - Force the full load of all albums before iterating over assets.
   - Explicitly call the appropriate method of the album collection to guarantee loading (could be access to the internal map, `load_full_albums` method, etc.).
   - Discuss and adjust the chosen method according to the current design.

2. **Improve timing logs:**
   - The log should have enough information (at `PROGRESS` level) to show how long each relevant phase takes:
     - Initial album loading (lite and full versions).
     - Iteration over all assets.
     - Tagging phase.
   - Record start and end times for each phase, and/or total elapsed time.
   - Consider if existing logs only need a level change to be visible in `PROGRESS` mode.

3. **Clarity in per-asset summary:**
   - Use the new log level `ASSET_SUMMARY` to record, for each processed asset:
     - Whether any action was performed (tagging, album change, etc.) or nothing was done.
     - Allow distinction between assets that required no changes and those that were modified.
   - Review and adjust existing logs so this summary is clear and useful.

## Justification

The ultimate goal is to debug and understand the performance and behavior of the algorithms, to release a stable version. The lack of clear log information and the complexity introduced by lazy-loading have made it difficult to identify problems and optimize the flow. Documenting and addressing these points will allow faster and more confident iteration.

## Next steps

- Review the current design of the album collection and choose the appropriate method to force full loading.
- Audit and improve timing logs and per-asset summaries.
- Implement changes and validate the impact on performance and flow clarity.

---

**This documentation serves as living context for future iterations and discussions about debugging and optimizing the loading and logging flow in the system.**
