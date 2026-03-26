# Subtask 003: Release Checklist

**Status:** Open  
**Created:** 2026-01-10

## Summary

Master checklist for final release preparation tasks. This covers all the items that need to be completed and verified before publishing a new release.

## Main Tasks


- [x] **Stability testing with incremental asset volumes** ([see subtask 002](subtasks/002-stability-testing-incremental-volumes/))
- [x] Review that the configuration is documented
- [?] Review the internal configuration (ensure we are not in debug mode)
- [x]deshabilitar no solo usar cache sino escribirla
- [x] Review the general documentation
- [ ] Update the CHANGELOG.md
- [ ] Review release workflow security in GitHub Actions ([see subtask 001](subtasks/001-github-actions-release-safety/))
// [ ] Review and refactor the hardcoded logic for the project root in `immich_autotag/run_output/manager.py` (function `get_run_output_dir`).
//      - Currently, the path is calculated rigidly; it should be flexible and reviewed before the release.

