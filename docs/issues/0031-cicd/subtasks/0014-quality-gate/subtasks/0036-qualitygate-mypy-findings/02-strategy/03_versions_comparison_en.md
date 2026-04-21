Title: Immich versions comparison — previous, target, latest

Summary

This document compares three Immich versions relevant to the current work: the version we were previously running (legacy), the version that introduced the breaking change we are adapting to (target), and the latest available release. The goal is to help decide whether to apply a minimal fix or to invest in upgrading to the latest release (and whether to update Postgres as part of that).

Comparison table

| Role | Version | Notable improvements | Breaking changes / API differences | Postgres compatibility | Effort to support in `immich-autotag` |
|---|---:|---|---|---|---|
| Previous (working) | v1.126.x (legacy) | Existing stable behavior: album DTO included embedded `assets` list; current autotag flow assumed `album.assets` present. | No change relative to current code. | Known to work with Postgres >=14. | None — current code works. |
| Target (current failure) | v1.127.x | Bug fixes and incremental features over v1.126; server moved heavy payloads to dedicated endpoints to reduce memory pressure. | Removed `assets` field from `AlbumResponseDto`; callers must call `GET /api/albums/{id}/assets` (paginated). Other small API shape changes possible in minor releases. | Same compatibility constraints as v1.x — Postgres 14 is supported. | Low: update code paths that iterate `album.assets` to call the new `album assets` endpoint (add pagination). Regenerate client if using generated SDK. Add tests. |
| Latest (up-to-date) | v2.7.5 (current latest as of April 2026) | Many features and performance improvements (asset viewer, duplicates, ML improvements), infrastructure changes; long-term support and active fixes. May include new CLI and tooling. | Potential breaking changes compared to v1.* (check release notes). May require schema/db migrations and review of server-client contract across many endpoints. | Immich supports Postgres >=14 and up to <19; recommended DB image variants include VectorChord/pgvector bundles (see Immich docs). | High: requires end-to-end validation, possible client/regeneration, check DB migrations, run integration tests, and handle any API contract diffs. Larger testing effort. |

Key notes
- The immediate runtime error in `immich-autotag` is caused by the v1.127.x change removing `album.assets`. The simplest fix is to replace uses of `album.assets` with explicit calls to the album-assets endpoint and iterate using pagination to avoid memory issues.
- v2.x is the current upstream stable major; it brings many improvements but also a larger upgrade surface (possible DB migrations, CLI/tooling changes and multiple endpoint changes). Upgrading to `v2.*` now would be a strategic investment with higher short-term cost and longer-term benefit.
- Postgres: current DB image uses Postgres 14 (VectorChord/pgvector variant). Immich supports Postgres >=14 and <19. Upgrading Postgres major version requires a dump/restore; switching the Immich DB image to a newer PostgreSQL major (e.g., 16) is possible but should be treated as a separate migration step.

Recommendation summary
- Short term (fast unblock): Implement the small compatibility patch for v1.127.x — call `GET /api/albums/{id}/assets` and iterate pages. Regenerate SDK if you rely on an `immich-client` generated from OpenAPI.
- Medium/long term (strategic): If you plan to maintain the project long-term, plan a planned upgrade to the latest `v2.*` release: schedule time to read the v1→v2 release notes, run a staging upgrade, and validate DB migrations and clients. Consider postponing Postgres major upgrades until after application-level compatibility is validated, unless upstream `v2` explicitly requires a newer Postgres major.

References
- Local repo notes: the failing analysis is documented in `02-strategy/gemini_response_en.md`.
- Immich releases: https://github.com/immich-app/immich/releases (latest series: v2.x)
- Immich docs: Postgres compatibility notes — supports Postgres >=14, <19 (VectorChord/pgvector guidance).
