
# Subtask 004: Memory Leak & Asset Wrapper Analysis

**Created:** 2026-01-27
**Status:** Open

## Context
- Excessive memory consumption and proliferation of `AssetResponseWrapper` and DTO instances detected.
- Profiling with `tracemalloc` shows millions of objects and memory usage over 2GB, mainly in JSON decoding and DTOs.
- The number of wrappers exceeds the number of unique assets (e.g., 1M wrappers vs. 350k assets).
- Uncertainty about cache effectiveness and deduplication.

## Findings
- DTOs (`AssetResponseDto`) are created when deserializing JSON, both from the API and from cache.
- Wrappers should be deduplicated by UUID in `AssetManager`, but there may be direct instantiations outside the manager.
- The cache stores serialized DTOs; if deserialization does not go through the manager, duplicates are generated.
- Profiling shows most memory is consumed in JSON decoding and DTO/wrapper creation.

## Hypotheses and Questions
- Is the manager always used to deduplicate wrappers?
- Is the cache helping or worsening the problem?
- Would processing in streaming/batches reduce consumption?
- Are there direct instantiations of wrappers in the code?

## Actions Taken
- Code has been audited and DTO/wrapper creation points identified.
- Logging controls have been suggested in the manager to detect duplicates.
- Cache and deduplication logic has been reviewed.
- Memory consumption has been compared between two `tracemalloc` snapshots.

## Next Steps
1. Add logging controls in the manager and wrapper constructor.
2. Audit and eliminate direct instantiations of wrappers outside the manager.
3. Review cache and deduplication logic after deserialization.
4. Optimize loading and processing (streaming/batches, free memory).
5. Document all findings and update this subtask.

## References
- [0021 - Profiling & Performance Reports](../)
- [Memory snapshots and analysis scripts](../../../..)
- [Relevant code: AssetManager, AssetResponseWrapper, asset_response_dto]

---
*Update this document with new findings, logs, and actions taken.*
