# Possible Actions: Memory Leak & Asset Wrapper Analysis

**Created:** 2026-01-27

## Action Options Table

| Option # | Action Description | Pros | Cons | Complexity | Impact | Notes |
|----------|-------------------|------|------|------------|--------|-------|
| 1 | Add logging in AssetManager and wrapper constructor to track instantiations and duplicates | Easy to implement, immediate feedback | May add overhead, only diagnostic | Low | Diagnostic | First step for visibility |
| 2 | Audit codebase for direct instantiations of AssetResponseWrapper and enforce manager usage | Ensures deduplication, prevents leaks | Requires code review, possible refactor | Medium | High | May require tests to verify |
| 3 | Refactor cache logic to ensure all DTOs/wrappers go through manager after deserialization | Fixes root cause of duplication | May require changes in cache and loading logic | Medium-High | High | Needs careful design |
| 4 | Implement streaming/batch processing for asset loading and processing | Reduces peak memory usage | May complicate logic, affects performance | High | Medium-High | Useful for large datasets |
| 5 | Optimize DTO structure to minimize memory footprint (e.g., use __slots__, reduce fields) | Direct memory savings | May break compatibility, needs migration | Medium | Medium | Should be benchmarked |
| 6 | Periodically free memory (del, gc.collect) after batch processing | Simple, can reduce fragmentation | Only partial solution, not root cause | Low | Low-Medium | Use with other actions |
| 7 | Profile and benchmark after each change to measure impact | Ensures changes are effective | Requires setup, may slow dev cycle | Low-Medium | Diagnostic | Should be continuous |

## Discussion Points
- Which actions are most feasible in the short term?
- Which have the highest potential impact?
- What risks or blockers exist for each?
- Should we prioritize diagnostic steps before refactoring?
- How will we measure success (metrics, profiling, regression tests)?

---
*Add comments, votes, and decisions below as the team discusses each option.*
