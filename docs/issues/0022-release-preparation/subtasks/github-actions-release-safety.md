# Subtask: Review GitHub Actions Release Safety

## Goal
Ensure that the GitHub Actions workflow for releases only triggers when intended, and cannot cause accidental releases.

## Checklist
- [ ] Review `.github/workflows/release.yml` triggers:
    - [ ] Confirm that releases are only triggered by version tags (e.g., `v*.*.*`) or manual dispatch.
    - [ ] Ensure no other branches or events can trigger a release by accident.
- [ ] Document the release process in the main checklist.
- [ ] Communicate to the team how to safely trigger a release and how to avoid accidental releases.
- [ ] Consider adding required approvals or branch protection if needed.

## Notes
- The current workflow triggers on version tags and manual dispatch only (see `release.yml`).
- If the release process changes, update this checklist accordingly.
