# Compatibility policy and convention

This document describes how Immich AutoTag releases indicate compatibility with Immich server versions, and how to update compatibility information when preparing a release.

Recommendation (convention):

- Each release entry in `CHANGELOG.md` SHOULD include a **Compatibility** section with:
  - **Tested with:** one or more exact Immich server tags used during validation (example: `v2.6.3`).
  - **Compatibility note:** a short sentence describing the supported range (example: "Compatible with Immich `v2.6.x`" or "Requires Immich `>=v2.6.0 <v3.0.0`").
  - Optionally, list known incompatible Immich versions.

- The release tag itself remains semantic (e.g. `v0.80.7`). Do NOT encode the Immich server version into the package tag; instead keep compatibility information inside the changelog and `docs/compatibility.md`.

Why this convention?

- Tags are for this project's versions and should follow semver.
- Compatibility is metadata about which external product versions this release was tested against.
- Keeping compatibility in docs avoids proliferation of tag formats and keeps `git describe` useful.

How to record compatibility when creating a release:

1. Decide the new package version (e.g. `0.80.7`).
2. Run tests against the target Immich server version(s) (record exact tag(s) used).
3. Add a `Compatibility` subsection to the new `CHANGELOG.md` entry with the tested Immich versions and a short compatibility range statement.
4. Optionally add a short note to the `README.md` or release notes on GitHub linking to `docs/compatibility.md`.

Automations:

- `setup_venv.sh` already attempts to detect the Immich server version to generate a compatible `immich-client`. This script will refuse to generate a client from `main` and insists on a concrete server tag — keep this behaviour.
- CI pipelines should run integration tests against at least one concrete Immich tag and record the tested tag as part of the release notes.

Example (CHANGELOG entry snippet):

### Compatibility
- **Tested with:** Immich `v2.6.3`.
- **Compatibility note:** Compatible with Immich `v2.6.x` (tested). If you run Immich `v2.5.x` or earlier, upgrade the server or use an earlier AutoTag release.

Maintainers: update this document when the project's compatibility policy changes.
