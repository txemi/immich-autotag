# Release Preparation Checklist

## Main Tasks

- [ ] Review the general documentation
- [ ] Review that the configuration is documented
- [ ] Update the CHANGELOG.md
- [ ] Review the internal configuration (ensure we are not in debug mode)
- [ ] Revisar la seguridad del workflow de release en GitHub Actions ([ver subtask](subtasks/github-actions-release-safety.md))
// [ ] Review and refactor the hardcoded logic for the project root in `immich_autotag/run_output/manager.py` (function `get_run_output_dir`).
//      - Currently, the path is calculated rigidly; it should be flexible and reviewed before the release.

## Notes
- Add subtasks in the `subtasks` folder if you need to break down any task.
