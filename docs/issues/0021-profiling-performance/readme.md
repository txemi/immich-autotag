# 0021 - Profiling & Performance Reports

**Status:** Proposed
**Created:** 2026-01-15
**Version:** v1.0

## Summary

Add formal profiling and performance-reporting support to the project and CI pipelines. When end-to-end runs become slow or regress, CI should automatically generate profiling reports and store them as build artifacts so developers can identify regressions quickly.

## Motivation

There are existing local profiling scripts, but no standardized CI integration. As the project grows, runtime regressions can go unnoticed. Centralizing profiling in CI enables continuous performance tracking, automatic regression detection, and easier triage.

## Goals

- Add CI tasks that run representative workloads and produce profiling output (CPU, wall time, memory, and flamegraphs or pprof-style reports).
- Store profiling artifacts in CI builds (Jenkins and GitHub Actions) for later download and analysis.
- Fail the build or add a warning if profiling metrics regress beyond configurable thresholds.
- Provide a minimal set of reproducible workload scripts for CI to execute (examples: profiling a full run on a small sample dataset, and profiling the classification step on N assets).

## Acceptance Criteria

- A `docs/issues/0021-profiling-performance/readme.md` describing the approach (this file).
- CI pipeline(s) updated to run profiling jobs and archive artifacts (example configs for Jenkins and GitHub Actions included or referenced).
- A short `scripts/profiling/README.md` or example script exists and runs in CI producing artifacts.
- A PR demonstrates profiling artifacts in CI for at least one pipeline run.

## Implementation Notes

- Use `pyinstrument`, `py-spy`, or `cProfile` + `snakeviz`/flamegraph tools for CPU profiling; `tracemalloc` or `memory_profiler` for memory.
- Start with a small sample dataset (committed test assets or synthetic sample) to keep CI time bounded.
- Archive artifacts using CI artifact store (GitHub Actions artifacts or Jenkins archived artifacts). Optionally upload to a storage bucket for long-term retention.
- Add a small `scripts/profiling/run_profile.sh` wrapper to make CI integration simpler.

## Risks

- Running full-scale profiling in CI may increase pipeline time; keep sample workloads small and representative.

## Next Steps

1. Add a small `scripts/profiling` example and a short CI job definition for GitHub Actions (or Jenkins) that runs it and archives artifacts.
2. Decide thresholds for regressions (e.g., 10% increase in median runtime of a representative workload).
3. Implement artifact retention policy and integrate with alerts if regressions are detected.

---

(If you'd like, I can add the example `scripts/profiling/run_profile.sh` and a GitHub Actions job YAML next.)
