# Active Run Monitoring — ai-context

**Last verified:** 2026-04-27

## Branch in use

Active branch: **`ops/batch-processing`**

The previous branch `fix/conversion-album-move` was merged to main (PR #57) and released
as `v0.80.10` on 2026-04-27. Operational batch runs were moved to a dedicated branch so
the `fix/*` namespace is not abused as a long-lived ops home. The first build on
`ops/batch-processing` starts with `skip_n=0` (one-time chain reset, ~1-2h overhead)
and chains forward from there.

The historical Jenkins job for `fix/conversion-album-move` remains accessible until the
multibranch orphan strategy purges it.

## Operational record (private repo)

The running historical table of builds (timestamps, agents, slice ranges, skip_n
chain, per-asset rates) is maintained in the private config repo, where machine
names, internal URLs and asset/album IDs can live unredacted:

```
~/.config/immich_autotag/issues/004-active-run-monitoring/
  README.md
  historical-runs.md
```

This public document focuses on strategy, decisions and reusable procedure.
The private one holds the data and concrete diagnosed cases.

---

## Context and overall strategy

The goal is to process the full Immich asset library (~400 000 assets) using a sequence
of short CI runs, each processing a fixed-size batch of 30 000 assets. Each run resumes
where the previous one left off via the checkpoint system.

**Why short runs instead of one long run:**
- The album map is loaded once at startup and becomes stale over time — multi-day or
  multi-hour runs end up operating on outdated data and produce incorrect results.
- Short runs (a few hours each) reload a fresh map every time.
- Shorter runs are much easier to diagnose: a failure or anomaly is contained to a
  smaller window and reproducible sooner.
- The checkpoint system handles continuity: each run saves its final position and the
  next one picks up from there (with a 100-asset overlap as safety margin).

**The manual workflow running in parallel (the user's side):**
Between CI runs, the user manually reviews the temporary "unclassified" albums that
the tool creates for assets it could not classify. The workflow is:

1. Filter temp albums (`*-autotag-temp-unclassified`) sorted by number of photos
2. Review those with more than 8 photos — decide whether to promote to a permanent
   album or move assets to the `autotag_input_meme` album (for meme content)
3. To avoid accidents, a new permanent album is created rather than reusing the temp one
4. The temp album is then deleted
5. Albums with 8 or fewer photos are left for now — they are too small to justify manual
   classification effort at this stage

**Signal that something is wrong:** if an album with more than 8 photos appears containing
assets that were already classified (e.g. already in a meme album, or already tagged with
`autotag_output_*`), that is a bug symptom, not expected behaviour. See the linked
incident below.

---

## Active incident being monitored

**Temp-unclassified albums incorrectly created for already-classified assets**

→ See full diagnosis and fix:
[`docs/issues/0024-album-features/subtasks/0016-auto-album-creation/subtasks/004-temp-album-false-positive-classified-assets/ai-context.md`](../../../../0024-album-features/subtasks/0016-auto-album-creation/subtasks/004-temp-album-false-positive-classified-assets/ai-context.md)

**Summary:** assets that had `autotag_input_meme` removed by a MOVE conversion were not
being added to the destination album when that album did not yet exist at processing time.
The tag was removed unconditionally even though the album assignment was silently skipped.
This left assets with no classification signal → they were placed in temp-unclassified
albums on subsequent runs.

**Status as of 2026-04-26:** fix implemented in `conversion_wrapper.py` and
`destination_wrapper.py`, pending review. The anomalous temp albums already created
require manual data remediation (re-tag assets or move them to the correct album).

---

## Why parallel execution was stopped (2026-04-26)

For a period, two CI agents were running builds concurrently on this branch. This caused:

- **Album map staleness**: both agents loaded their map at start and then operated on
  independent snapshots. Actions by one build were invisible to the other.
- **Checkpoint conflicts**: both builds wrote their `run_stats.yaml` independently;
  the next run could pick up the checkpoint from either, leading to gaps or double
  processing.
- **Duplicate temp albums**: both builds could create the same temp album name
  concurrently, producing the duplicate-name conflicts visible in early build logs.
- **Unclear root cause**: with two parallel runs it was impossible to tell whether
  anomalous behaviour (e.g. temp albums for already-classified assets) came from a
  software bug or from the parallel execution interference.

**Resolution:** the second CI agent node was taken offline. From 2026-04-26 onwards,
only one build runs at a time. This makes runs deterministic and fully reproducible.

---

## What we are tracking

Branch `ops/batch-processing` is being executed sequentially by Jenkins.
Each run should:
- Process exactly `max_assets = 30 000` assets
- Resume from the checkpoint left by the previous run (`resume_previous = true`, overlap = 100)
- Push a `jenkins-success-<N>-<sha>` git tag to GitHub on success (pending GitHub App
  permission fix — currently the app only has read access)

---

## How to verify a run is healthy

From the console log, look for:
- `[PERF]` lines: `Processed:<session_count>/...` — session_count should grow from ~0 to ~30 000
- `Skip:<N>` — N should match the `count` from the previous run minus the overlap (~100)
- `Remaining:` — should be positive and decreasing (negative = bug, see fixes below)
- `abs_end` in PERF (builds from commit `4247e1e6` onwards) — shows the absolute
  endpoint of this slice, e.g. `37775(abs_count)/48700(abs_end)` meaning "at 37775,
  stopping at 48700 out of 403746 total"
- Final line: `Total assets processed: 30000`
- No new temp-unclassified albums created for assets that were already classified
  (**observation mode** — sequential runs will determine if this was a parallelism issue
  or a code bug; see [linked incident](../../../../0024-album-features/subtasks/0016-auto-album-creation/subtasks/004-temp-album-false-positive-classified-assets/ai-context.md))

---

## Fixes applied in this session (2026-04-25 / 2026-04-26)

### fix(perf): negative remaining time with skip_n — `95daca3f`
- **File:** `immich_autotag/statistics/statistics_manager.py`
- **Root cause:** `run_stats.count` stores `skip_n + session_count` (correct for
  checkpoint resume), but `PerformanceTracker` expected only `session_count`.
  Caused `remaining < 0` on every resumed run.
- **Fix:** `_to_session_count()` helper subtracts `skip_n` before passing to tracker.

### fix(ci): Jenkins GitHub tagging via HTTPS — `66a26278`
- **File:** `Jenkinsfile`
- **Root cause:** `tagBuild()` used SSH but the CI agent has no GitHub SSH deploy key.
- **Fix:** replaced SSH block with `withCredentials` using the HTTPS credential already
  used for checkout.
- **Remaining issue:** the GitHub App only has read access → push returns 403.
  Fix: grant `Contents: Read and write` to the app in GitHub repository settings.

### feat(perf): abs_end in PERF log when processing a slice — `4247e1e6`
- **File:** `immich_autotag/utils/perf/performance_tracker.py`
- **Change:** when `skip_n > 0`, PERF line now shows `abs_end = skip_n + total_to_process`
  so it is immediately visible where the current slice ends in absolute terms.

---

## Checkpoint mechanics (how resume works)

See `immich_autotag/statistics/checkpoint_manager.py` and
`immich_autotag/statistics/_find_max_skip_n_recent.py`.

- At end of each run, `run_stats.count = skip_n + session_count` is saved to YAML.
- Next run reads recent YAMLs, takes max `count`, subtracts overlap of 100 → new `skip_n`.
- Chain: run 1 ends at ~30 000 → run 2 starts at skip_n ~29 900 → run 2 ends at ~60 000 → …

---

## What to do if a run looks wrong

| Symptom | Likely cause | Where to look |
|---|---|---|
| `Remaining:` is negative | Old code without `95daca3f` | Check deployed commit |
| `Skip:0` when it should resume | Checkpoint YAML not found or >3h old | `logs_local/` on the CI agent |
| Tag not pushed (403) | GitHub App missing write permission | GitHub repo → Settings → GitHub Apps |
| `Total assets processed: N` where N < 30 000 | Run aborted or timed out | Abort reason in log |
| Temp album created for a classified meme asset | Bug in `conversion_wrapper.py` not yet deployed, or data remediation needed | See incident link above |
| Two builds show same `Skip:N` | Parallel execution or stale checkpoint | Confirm sequential-only mode is active |

---

## Diagnostic procedure for a single suspect asset

When a user reports a specific asset that looks misclassified or stuck in the wrong
album (e.g. has the meme tag but is in a temp-unclassified album), follow this:

1. **Search Jenkins logs for the asset ID and the album name**
   - Loop the recent builds (`curl .../consoleText | grep <asset-id>` and the album
     name) — the album ID alone usually does NOT appear, because albums are logged
     by name.
   - **No matches** → the asset has not been processed in any retained run yet. It
     is legacy state. Wait for the next slice that covers it. Stop here.
   - **Matches** → continue.

2. **Query Immich API directly for the current state**
   - Credentials live in `~/.config/immich_autotag/config.py` (`server.host`,
     `server.port`, `server.api_key`).
   - Tags: `GET /api/assets/{id}` → field `tags`
   - Albums: `GET /api/albums?assetId={id}`
   - Header: `x-api-key: <key>`

3. **Cross-check with the classification rules** (in the same config)
   - Rule matching is **OR** between `tag_names`, `album_name_patterns`, `asset_links`.
     A single matching tag is enough.
   - See linked incident for full semantics:
     [`004-temp-album-false-positive-classified-assets/ai-context.md`](../../../../0024-album-features/subtasks/0016-auto-album-creation/subtasks/004-temp-album-false-positive-classified-assets/ai-context.md)

4. **Conclude**
   - The asset *should* match a rule but doesn't → real bug, gather log evidence
   - The asset matches but log shows it stayed in temp → real bug, gather log evidence
   - The asset is legacy state and hasn't been touched yet → wait
   - The asset has stale `autotag_output_*` tags from past runs → expected legacy,
     will clean up on next traversal
