# Subtask 003: Release Checklist

**Status:** Open  
**Created:** 2026-01-10

## Summary

Master checklist for final release preparation tasks. This covers all the items that need to be completed and verified before publishing a new release.

## Main Tasks

- [ ] Review the general documentation
- [ ] Review that the configuration is documented
- [ ] Update the CHANGELOG.md
- [ ] Review the internal configuration (ensure we are not in debug mode)
- [ ] Revisar la seguridad del workflow de release en GitHub Actions ([ver subtask 001](subtasks/001-github-actions-release-safety/))
- [ ] **Stability testing with incremental asset volumes** ([ver subtask 002](subtasks/002-stability-testing-incremental-volumes/))
// [ ] Review and refactor the hardcoded logic for the project root in `immich_autotag/run_output/manager.py` (function `get_run_output_dir`).
//      - Currently, the path is calculated rigidly; it should be flexible and reviewed before the release.

