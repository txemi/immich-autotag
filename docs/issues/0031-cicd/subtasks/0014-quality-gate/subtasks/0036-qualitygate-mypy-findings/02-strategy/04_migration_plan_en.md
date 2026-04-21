Title: Migration plan — short and long term options

Objective

Provide a concise, actionable migration plan covering (A) the fastest fix to restore compatibility with the server version that removed `album.assets` and (B) the recommended steps to upgrade to the latest Immich release and evaluate Postgres upgrade.

Option A — Quick fix (recommended immediate action)
- Goal: unblock production and make code tolerant to v1.127.x server behavior.
- Steps:
  1. Locate codepaths accessing `album.assets` (search `album.assets` and `for asset in album.assets`).
  2. Replace with an explicit helper that fetches assets via `GET /api/albums/{id}/assets` and yields items with pagination (use page/size and small batches, e.g., 5k or 1k depending on memory).
  3. If using a generated `immich-client`, regenerate the SDK (the project has `setup_venv.sh` that fetches OpenAPI specs) and import the new `get_album_assets` method if available.
  4. Add unit / integration tests mocking an album response without `assets` and the album-assets paginated response.
  5. Deploy to staging and validate processing of a large album (spot-check memory and runtime). Roll out to production once stable.

Time & risk estimate (Option A)
- Time: 1–2 engineer-days (dev + tests + staging validation).
- Risk: Low — small surface change. No DB changes. Minimal downtime risk.

Option B — Upgrade to latest Immich (strategic)
- Goal: migrate to v2.* (latest) for long-term improvements and active upstream fixes.
- Preconditions: backup current DB; run staging environment; read v1→v2 release notes for breaking changes.
- High-level steps:
  1. Read release notes for each intermediate major/minor between current server and target `v2.*`. Identify required database migrations, endpoint deprecations, and schema changes.
  2. Provision a staging environment with identical DB snapshot (restore a copy), and run Immich `v2.*` containers on staging.
  3. Regenerate the OpenAPI client (`immich-client`) against the chosen v2 OpenAPI spec. Update `immich-autotag` code to match any endpoint or DTO changes (e.g., album/asset endpoints, auth, ML endpoints).
  4. Run database migrations triggered by the server image; validate app behavior and automated tests.
  5. If DB image upgrade required (Postgres major bump), perform DB major upgrade as a separate step: dump/restoredb to new major, or follow Immich DB image upgrade guidance. Validate VectorChord/pgvector compatibility.
  6. Smoke-test ML flows, large-album processing, and any background jobs.
  7. Plan a maintenance window and production cutover; have rollback plan (DB backups, old image tags).

Time & risk estimate (Option B)
- Time: 2–6+ engineer-days depending on complexity and number of breaking changes found. If a Postgres major upgrade is necessary, add extra time for dump/restore and validation (1–2 days more). 
- Risk: Medium to High — schema changes and unknown client-server contract changes could surface issues.

Postgres upgrade guidance
- Immich supports Postgres >=14 and <19. The project's docker-compose already runs a `ghcr.io/immich-app/postgres:14-vectorchord...` image. Upgrading the Postgres major version (14 → 16 or 18) requires a dump/restore (pg_dump / pg_restore) — plan for downtime or a rolling migration strategy.
- If you only upgrade Immich (server) to v2.* and the server still supports Postgres 14, you can postpone Postgres major upgrades until after application compatibility is validated.

Suggested next steps (I can do these)
1. Implement Option A patch (I can prepare a PR that replaces `album.assets` usages and adds a paginated iterator helper).
2. Regenerate `immich-client` against the detected OpenAPI spec and run unit tests locally.
3. If you prefer the strategic path, I can draft a detailed upgrade checklist for v1→v2 including the specific release notes to review and a staging runbook.
