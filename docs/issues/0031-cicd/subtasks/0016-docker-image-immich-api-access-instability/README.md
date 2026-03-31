# 0016 · Docker Image Immich API Access Instability

## Status

Open

## Context

During release preparation, the application is stable in Jenkins and python package distribution is working as expected. However, the latest published Docker image (`0.80.3`) shows intermittent failures when trying to reach the Immich API in some environments.

## Problem Statement

The Docker image `0.80.3` may fail to access the Immich API endpoint in specific user setups.

Observed behavior:
- Works reliably in Jenkins and CI-related execution paths.
- Fails in some external/runtime environments when the container tries to call the Immich API.
- The exact root cause is not yet confirmed.

Potential hypotheses:
- DNS resolution differences between environments.
- Network/container runtime configuration differences.
- Host-specific routing or name resolution behavior.

## Impact

- A subset of users may experience runtime failures with the Docker image.
- This does not fully block release progression, but it must be tracked as an active bug.

## Release Decision

Proceed with the next release while explicitly recording this known issue for follow-up.

## Scope

Included:
- Register and track the Docker access instability as a formal subtask.
- Document current symptoms and working hypotheses.
- Keep release flow unblocked while preserving traceability.

Excluded:
- Root-cause confirmation and final fix (handled in follow-up work).

## Initial Follow-up Plan

1. Reproduce the issue in a controlled Docker runtime outside Jenkins.
2. Compare DNS/network behavior between failing and working environments.
3. Add diagnostics to startup/API access path (host resolution and connectivity logs).
4. Validate fixes against the same `0.80.3` scenario and future image builds.

## Cross-References

- Parent issue: `docs/issues/0031-cicd/`
- Release preparation context: `docs/issues/0022-release-preparation/`
- GitHub incident: `https://github.com/txemi/immich-autotag/issues/43`

## Notes

This entry is created to keep release governance explicit: known risk is documented, traceable, and planned for resolution.
