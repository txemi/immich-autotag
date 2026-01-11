# Issue 0013: git_version is null in statistics output

## Context

When reviewing the statistics output, we observed that the field `git_version` appears as `null` in some runs, while in others, fields like `git_describe_runtime` and `git_describe_package` are present and correctly populated (e.g., `v0.60.0-17-gd1e8b97-dirty`).

### Example 1 (problematic):
```
git_version: null
album_date_mismatch_count: 684
update_asset_date_count: 0
...existing code...
```

### Example 2 (expected):
```
git_describe_runtime: v0.60.0-17-gd1e8b97-dirty
git_describe_package: v0.60.0-0-gcb57d13-dirty
album_date_mismatch_count: 1
update_asset_date_count: 0
...existing code...
```

## Problem
- In some statistics outputs, `git_version` is `null` instead of showing the expected git description fields.
- This may indicate a code path or environment where git information is not being captured or written correctly.

## Tasks
- [ ] Investigate why `git_version` is sometimes `null`.
- [ ] Ensure that the correct git description fields (`git_describe_runtime`, `git_describe_package`) are always present in the statistics output.
- [ ] Update the code to standardize the output and avoid legacy/obsolete fields.
- [ ] Document findings and update this issue with the root cause and solution.

## Additional Diagnostic Information

- When running the code directly from a local git repository, the expected git version fields (`git_describe_runtime`, `git_describe_package`) are present and correctly populated.
- When running the published Docker image from the registry, the problematic case occurs: `git_version` is `null` and the expected git description fields are missing.
- This suggests the issue is related to how git metadata is captured or embedded during the Docker build or runtime process.

## References
- Example statistics files: see logs_local/20260111_153050_PID812172/run_statistics.yaml and other recent runs.

---

*Created automatically by GitHub Copilot at user request. Please update with findings and resolution.*
